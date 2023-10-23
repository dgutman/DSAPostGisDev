from girder_client import GirderClient, HttpError
import numpy as np
import cv2 as cv
from PIL import Image
from io import BytesIO


def login(apiurl, username=None, password=None):
    """Authenticate girder client instance.

    Args:
        apiurl: API URL.
        username: Username.
        password: Password.

    Returns:
        gc: Girder client.

    """
    gc = GirderClient(apiUrl=apiurl)

    if username is None or password is None:
        interactive = True
    else:
        interactive = False

    gc.authenticate(username=username, password=password, interactive=interactive)

    return gc


def get_items(gc, parent_id, limit=25):
    """Recursively gets items in a collection or folder parent location.

    Args:
        gc: Girder client.
        parent_id: Folder or collection id.

    Returns:
        items: Items

    """
    try:
        items = gc.get(
            f"resource/{parent_id}/items?type=collection&limit={limit}&sort="
            + "_id&sortdir=1"
        )
    except HttpError:
        items = gc.get(
            f"resource/{parent_id}/items?type=folder&limit=0&sort=_id&" + "sortdir=1"
        )

    return items


def scale_contours(contours, sf):
    """Scale contours.

    Args:
        contours: List of (x, y) contours.
        sf: Scale factor.

    Returns:
        Contours after scaling.

    """
    for i, contour in enumerate(contours):
        contours[i] = (contour * sf).astype(contour.dtype)

    return contours


def get_annotations_documents(gc, item_id, doc_names=None, groups=None):
    """Get Histomics annotations for an image.

    Args:
        gc: Girder client.
        item_id: Item id.
        doc_names: Only include documents with given names.
        groups : Only include annotation documents that contain at least one
            annotation of these set of groups.

    Returns:
        List of annotation documents.

    """
    if isinstance(doc_names, str):
        doc_names = [doc_names]

    if isinstance(groups, str):
        groups = [groups]

    annotation_docs = []

    # Get information about annotation documents for item.
    for doc in gc.get(f"annotation?itemId={item_id}"):
        # If needed only keep documents of certain names.
        if doc_names is not None and doc["annotation"]["name"] not in doc_names:
            continue

        # Filter out documents with no annotation groups.
        if "groups" not in doc or not len(doc["groups"]):
            continue

        # Ignore document if it does not contain elements in the group list.
        if groups is not None:
            ignore_flag = True

            for group in doc["groups"]:
                if group in groups:
                    ignore_flag = False
                    break

            if ignore_flag:
                continue

        # Get the full document with elements.
        doc = gc.get(f"annotation/{doc['_id']}")

        # Filter document for elements in group only.
        elements_kept = []
        doc_groups = set()

        for element in doc["annotation"]["elements"]:
            # Remove element without group.
            if "group" not in element:
                continue

            if groups is None or element["group"] in groups:
                elements_kept.append(element)
                doc_groups.add(element["group"])

        doc["groups"] = list(doc_groups)
        doc["annotation"]["elements"] = elements_kept

        # Add doc if there were elements.
        if len(elements_kept):
            annotation_docs.append(doc)

    return annotation_docs


def get_thumbnail(gc, item_id, shape=None, fill=None):
    """Get thumbnail image of WSI and a binary mask from annotations.

    Args:
        gc: Girder client.
        item_id: DSA WSI id.
        shape: Width x height of thumbnail returned. If fill is not
            specified then width is prioritized to keep same aspect ratio
            of WSI.
        fill: RGB fill to return thumbnail in the exact same aspect ratio
            of shape parameter.

    Returns:
        Thumbnail image and binary mask.

    """
    # Get thumbnail image.
    request = f"item/{item_id}/tiles/thumbnail?"

    if shape is not None:
        request += f"width={shape[0]}&height={shape[1]}"

    if fill is not None:
        request += f"&fill=rgb({fill[0]}%2C{fill[1]}%2C{fill[2]})"

    request += "&encoding=PNG"

    thumbnail = np.array(Image.open(BytesIO(gc.get(request, jsonResp=False).content)))

    return thumbnail


def get_tile_metadata(gc, item_id):
    """Get the tile source metadata for an item with a large image
    associated with it.

    Args:
        gc: Girder client.
        item_id: DSA WSI id.

    Returns:
        Metadata for large image associated.

    """
    return gc.get(f"item/{item_id}/tiles")


def get_contours_from_annotations(annotation_docs):
    """Extract polyline annotation elements as contours-like arrays from
    a list of annotaiton documents.

    Args:
        Annotation documents.

    Returns:

    """
    contours = []

    for doc in annotation_docs:
        ann = doc.get("annotation", {})

        if "element" in ann:
            for element in doc["annotation"]["elements"]:
                if element["type"] == "polyline":
                    contour = []

                    for xyz in element["points"]:
                        contour.append([int(xyz[0]), int(xyz[1])])

                    contour = np.array(contour, dtype=int)

                    if len(contour) > 2:
                        contours.append(contour)

    return contours


def get_thumbnail_with_mask(
    gc,
    doc,
    size,
    annotation_docs=None,
    annotation_groups=None,
    fill=None,
    return_contour=False,
):
    """Get thumbnail image of WSI and a binary mask from annotations.

    Args:
        gc: Girder client.
        item_id: DSA WSI id.
        size: Size of thumbnail returned.
        annotation_docs: Filter to annotation documents of this name / these
            names.
        annotation_groups: Filter to annotations from this group / these
            groups.
        fill: RGB fill when specifying both width and height of different
            aspect ratio than WSI.
        return_contour: True to return contours as well.

    Returns:
        Thumbnail image and binary mask. If return_contour is True then it also
        returns the scaled down contours.

    """
    # Annotation documents.
    # annotation_docs = get_annotations_documents(
    #     gc, item_id, doc_names=annotation_docs, groups=annotation_groups
    # )

    thumbnail = get_thumbnail(gc, doc["itemId"], shape=(size, size))

    # Extract annotation elements as contours.
    contours = get_contours_from_annotations([doc])

    # Get shape of the WSI.
    tile_metadata = get_tile_metadata(gc, doc["itemId"])

    # Downscale contours to thumbnail size.
    mask = np.zeros(thumbnail.shape[:2], dtype=np.uint8)
    sf = mask.shape[1] / tile_metadata["sizeX"]

    contours = scale_contours(contours, sf)

    # Draw the contours on mask.
    mask = cv.drawContours(mask, contours, -1, 255, cv.FILLED)

    # Pad the image to be the right shape.
    if fill is not None:
        h, w = mask.shape[:2]

        thumbnail = cv.copyMakeBorder(
            thumbnail, 0, size - h, 0, size - w, cv.BORDER_CONSTANT, value=fill
        )
        mask = cv.copyMakeBorder(
            mask, 0, size - h, 0, size - w, cv.BORDER_CONSTANT, value=0
        )

        if return_contour:
            return thumbnail, mask, contours
        else:
            return thumbnail, mask
    return thumbnail, mask
