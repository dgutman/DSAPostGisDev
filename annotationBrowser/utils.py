from girder_client import GirderClient, HttpError
import numpy as np
import cv2 as cv
from PIL import Image
from io import BytesIO
from multiprocessing import Pool
from typing import List, Union, Tuple
from pandas import DataFrame, concat
from typing import Tuple
from pandas import DataFrame
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from skimage.feature import blob_dog, blob_log, blob_doh
from math import sqrt
from os import makedirs
from os.path import isfile, join
from os.path import basename, splitext
from typing import Union, Tuple
import numpy as np
import torch
from tqdm.notebook import tqdm

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
    try:
        thumbnail = np.array(
            Image.open(BytesIO(gc.get(request, jsonResp=False).content))
        )
    except:
        print("Thumbnail pull failled")
        return None
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

def imread(fp: str, fmt: str = 'rgb', grayscale: bool = False) -> np.ndarray:
    
    assert fmt in ('rgb', 'bgr', 'gray'), "fmt must be 'rgb', 'bgr' or 'gray'."
    
    if grayscale:
        return cv.imread(fp, cv.IMREAD_GRAYSCALE)
    
    img = cv.imread(fp)
    
    if fmt == 'rgb':
        return cv.cvtColor(img, cv.COLOR_BGR2RGB)
    elif fmt == 'gray':
        return cv.cvtColor(img, cv.IMREAD_GRAYSCALE)
    else:
        return img


def read_yolo_label(
    fp: str, img_shape: Union[int, Tuple[int, int], None] = None, 
    shift: Union[int, Tuple[int, int], None] = None, 
    convert: bool = False
) -> np.ndarray:
    """Read a yolo label text file. It may contain a confidence value for the 
    labels or not, will handle both cases
    
    Args:
        fp (str): The path of the text file.
        img_shape (Union[int, Tuple[int, int], None]): Image width and 
            height corresponding to the label, if an int it is assumed both 
            are the same. Will scale coordinates to int values instead of 
            normalized if given.
        shift (Union[int, Tuple[int, int], None]): Shift value in the x and 
            y direction, if int it is assumed to be the same in both. These 
            values will be subtracted and applied after scaling if needed. 
        convert (bool): If True, convert the output boxes from yolo format 
            (label, x-center, y-center, width, height, conf) to (label, x1, y1, 
            x2, y2, conf) where point 1 is the top left corner of box and point 
            2 is the bottom corner of box.
    
    Returns:
        (np.ndarray) Coordinates array, [N, 4 or 5] depending if confidence was
        in input file.
    
    """
    coords = []
    
    with open(fp, 'r') as fh:
        for line in fh.readlines():
            if len(line):
                coords.append([float(ln) for ln in line.strip().split(' ')])
                
    coords = np.array(coords)
    
    # scale coords if needed
    if img_shape is not None:
        if isinstance(img_shape, int):
            w, h = img_shape, img_shape
        else:
            w, h = img_shape[:2]
            
        coords[:, 1] *= w
        coords[:, 3] *= w
        coords[:, 2] *= h
        coords[:, 4] *= h
        
    # shift coords
    if shift is not None:
        if isinstance(shift, int):
            x_shift, y_shift = shift, shift
        else:
            x_shift, y_shift = shift[:2]
            
        coords[:, 1] -= x_shift
        coords[:, 2] -= y_shift
        
    if convert:
        coords[:, 1:5] = convert_box_type(coords[:, 1:5])
        
    return coords



def im_to_txt_path(impath: str, txt_dir: str = '/labels/', ext='txt'):
    """Replace the last occurance of /images/ to /labels/ in the given image 
    path and change extension to .txt
    
    Args:
        impath: Filepath to image.
        txt_dir: Replace last occurence of '/images/' with this value.
        ext: Replace with this extension.
    
    Returns:
        Updated filepath.
    
    """
    splits = impath.rsplit('/images/', 1)
    return splitext(f'/{txt_dir}/'.join(splits))[0] + f'.{ext}'

def corners_to_polygon(x1: int, y1: int, x2: int, y2: int) -> Polygon:
    """Return a Polygon from shapely with the box coordinates given the top left and bottom right corners of a 
    rectangle (can be rotated).
    
    Args:
        x1, y1, x2, y2: Coordinates of the top left corner (point 1) and the bottom right corner (point 2) of a box.
        
    Returns:
        Shapely polygon object of the box.
        
    """
    return Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
    
def tile_roi_with_labels(
    fp: str, save_dir: str, tile_size: int = 1280, stride: int = None, 
    boundary_thr: float = 0.2, fill: Tuple[int] = (114, 114, 114), 
    box_thr: float = 0.5, grayscale: bool = False
) -> DataFrame:
    """Tile an ROI image with labels.
    
    Args:
        fp: Image filepath, should be in an '/images/ directory'.
        save_dir: Location to save images and labels.
        tile_size: Size of tile, uses square tiles only.
        stride: Stride to use when tiling, if None then it is set equal to 
            tile_size (no overlap between tiles).
        boundary_thr: If ROI has a boundary (for rotated ROIs) then a tile must
            have sufficient area in boundary to be included (0.0 - 1.0).
        fill: RGB when padding image.
        box_thr: Area threshold of box that must be in a tile.
        grayscale: True to treat images as grayscale.
       
    Returns:
        Metadata of tiles saved.
        
    """
    # read the image
    print(fp)
    img = imread(fp, grayscale=grayscale)
    h, w = img.shape[:2]
    
    # look for labels and boundaries
    label_fp = im_to_txt_path(fp)
    boundary_fp = im_to_txt_path(fp, txt_dir='boundaries')
    
    if isfile(label_fp):
        labels = read_yolo_label(label_fp, img_shape=(w, h), convert=True)
    else:
        labels = []
    
    # Convert the labels into a GeoDataFrame.
    label_df = []
    
    for box in labels:
        label = box[0]
        x1, y1, x2, y2 = box[1:5].astype(int)
        
        label_df.append([label, x1, y1, x2, y2, 
                         corners_to_polygon(x1, y1, x2, y2)])
        
    label_df = GeoDataFrame(
        label_df, 
        columns=['label', 'x1', 'y1', 'x2', 'y2', 'geometry']
    )
    label_areas = label_df.area
    
    # For the boundary, create a polygon object.
    if isfile(boundary_fp):
        # format the boundaries in to a countour shape
        with open(boundary_fp, 'r') as fh:
            boundaries = [float(c) for c in fh.readlines()[0].split(' ')]
            
        # scale to the image size.
        roi = Polygon(
            (np.reshape(boundaries, (-1, 2)) * [w, h]).astype(int)
        )
    else:
        # Default: the whole image is the ROI.
        roi = corners_to_polygon(0, 0, w, h)  
    
    img_dir = join(save_dir, 'images')
    label_dir = join(save_dir, 'labels')
    makedirs(img_dir, exist_ok=True)
    makedirs(label_dir, exist_ok=True)
    
    # Default stride is no-overlap.
    if stride is None:
        stride = tile_size  # default behavior - no overlap
    
    # Pad the image to avoid getting tiles not of the right size.
    img = cv.copyMakeBorder(img, 0, tile_size, 0, tile_size, cv.BORDER_CONSTANT, 
                            value=fill)
    
    # Get the top left corner of each tile.
    xys = list(((x, y) for x in range(0, w, stride) 
                for y in range(0, h, stride)))
        
    tile_df = []  # track tile data.

    # Pre-calculate the number of pixels in tile that must be in ROI to include.
    intersection_thr = tile_size**2 * boundary_thr
    
    # loop through each tile coordinate
    for xy in xys:
        # Check if this tile is sufficiently in the boundary.
        x1, y1 = xy
        x2, y2 = x1 + tile_size, y1 + tile_size
        
        tile_pol = corners_to_polygon(x1, y1, x2, y2)
        intersection = roi.intersection(tile_pol).area
        
        if intersection > intersection_thr:
            # Get the tile image.
            tile = img[y1:y2, x1:x2]
            
            # Create a name for the tile image / label.
            fn = f'{get_filename(fp)}-x{x1}y{y1}.'
            
            img_fp = join(img_dir, fn + 'png')
            
            tile_df.append([img_fp, fp, x1, y1, tile_size])
            
            if not isfile(img_fp):
                imwrite(img_fp, tile, grayscale=grayscale)
                
            # Find all boxes that intersect
            label_intersection = label_df.geometry.intersection(tile_pol).area
            
            tile_boxes = label_df[label_intersection / label_areas > box_thr]
            
            # save these as normalized labels, threshold the box edges.
            if len(tile_boxes):
                labels = ''
                
                for _, r in tile_boxes.iterrows():
                    # Shift coordinates to be relative to this tile.
                    xx1 = np.clip(r.x1 - x1, 0, tile_size) / tile_size
                    yy1 = np.clip(r.y1 - y1, 0, tile_size) / tile_size 
                    xx2 = np.clip(r.x2 - x1, 0, tile_size) / tile_size
                    yy2 = np.clip(r.y2 - y1, 0, tile_size) / tile_size

                    xc, yc = (xx1 + xx2) / 2, (yy1 + yy2) / 2
                    bw, bh = xx2 - xx1, yy2 - yy1
                    labels += f'{r.label} {xc:.4f} {yc:.4f} {bw:.4f} {bh:.4f}\n'
                    
                with open(im_to_txt_path(img_fp), 'w') as fh:
                    fh.write(labels.strip())
                    
    return DataFrame(tile_df, columns=['fp', 'roi_fp', 'x', 'y', 'tile_size'])


def tile_roi_with_labels_wrapper(
    fps: List[str], save_dir: Union[str, List[str]], tile_size: int = 1280, 
    stride: int = None, boundary_thr: float = 0.2, nproc: int = 10,
    fill: Tuple[int] = (114, 114, 114), box_thr: float = 0.5, 
    notebook: bool = False, grayscale: bool = False
) -> DataFrame:
    """Tile an ROI image with labels.
    
    Args:
        fps: Image filepaths, should be in an '/images/ directory'.
        save_dir: Either a single location to create images and labels dir or
            a list of directories for each filepath passed.
        tile_size: Size of tile, uses square tiles only.
        stride: Stride to use when tiling, if None then it is set equal to 
            tile_size (no overlap between tiles).
        boundary_thr: If ROI has a boundary (for rotated ROIs) then a tile must
            have sufficient area in boundary to be included (0.0 - 1.0).
        nproc: Number of parallel processed to use.
        fill: RGB when padding image.
        box_thr: Area threshold of box that must be in a tile.
        notebook: Select which type of tqdm to use.
        grayscale: True to treat images as grayscale.
        
    Returns:
        Metadata of tiles saved.
        
    """
    if isinstance(save_dir, (list, tuple)):
        if len(save_dir) != len(fps):
            raise Exception('If save_dir is a tuple / list, then it must be the '
                            'same length as the number of filepaths.')
    else:
        save_dir = [save_dir] * len(fps)
    
    if notebook:
        from tqdm.notebook import tqdm
    else:
        from tqdm import tqdm
        
    with Pool(nproc) as pool:
        jobs = [
            pool.apply_async(
                func=tile_roi_with_labels, 
                args=(
                    fp, sd, tile_size, stride, boundary_thr, fill, box_thr,
                    grayscale
                )) 
            for fp, sd in zip(fps, save_dir)]
        
        tile_df = [job.get() for job in jobs]
        
    return concat(tile_df, ignore_index=True)
def imwrite(fp: str, img: np.ndarray, grayscale: bool = False):
    """Write image to file.
    
    Args:
        fp: Filepath to save image.
        img: Image to save.
        grayscale: True to save image as a grayscale image, otherwise it is
            saved as an RGB image.
    
    """
    if grayscale:
        cv.imwrite(fp, img)
    else:
        cv.imwrite(fp, cv.cvtColor(img, cv.COLOR_RGB2BGR))
def imread(fp: str, fmt: str = 'rgb', grayscale: bool = False) -> np.ndarray:
    """
    Read image file*.

    * Only supports RGB images currently, in the future we will look add 
    support for RGBA and grayscale images.
    
    Args:
        fp (str): Filepath to image.
        fmt (str): Format to read image as: 'rgb', 'bgr', 'gray'.
        grayscale (bool): Will be deprecated in the future, similar behavior can
            be achieved by setting format to 'gray'. Read image as grayscale.
    
    Returns:
        (numpy.ndarray) Image as numpy array.
    
    """
    assert fmt in ('rgb', 'bgr', 'gray'), "fmt must be 'rgb', 'bgr' or 'gray'."
    
    if grayscale:
        return cv.imread(fp, cv.IMREAD_GRAYSCALE)
    
    img = cv.imread(fp)
    
    if fmt == 'rgb':
        return cv.cvtColor(img, cv.COLOR_BGR2RGB)
    elif fmt == 'gray':
        return cv.cvtColor(img, cv.IMREAD_GRAYSCALE)
    else:
        return img

def convert_box_type(box: np.ndarray) -> np.ndarray:
    """Convert a box type from YOLO format (x-center, y-center, box-width,
    box-height) to (x1, y1, x2, y2) where point 1 is the top left corner of box 
    and point 2 is the bottom right corner.
    
    Args:
        box (np.ndarray): [N, 4], each row a point and the format being 
            (x-center, y-center, box-width, box-height).
        
    Returns:
        new_box (np.ndarray): [N, 4] each row a point and the format x1, y1, x2,
        y2.
        
    """
    # get half the box height and width
    half_bw = box[:, 2] / 2
    half_bh = box[:, 3] / 2
    
    new_box = np.zeros(box.shape, dtype=box.dtype)
    new_box[:, 0] = box[:, 0] - half_bw
    new_box[:, 1] = box[:, 1] - half_bh
    new_box[:, 2] = box[:, 0] + half_bw
    new_box[:, 3] = box[:, 1] + half_bh
    
    return new_box

def get_filename(fp: str, prune_ext: bool = True) -> str:
    """Get the filename of a filepath.

    Args:
        fp: Filepath.
        prune_ext: Remove extension.
    
    Returns:
        Filename.

    """
    fn = basename(fp)

    if prune_ext:
        fn = splitext(fn)[0]

    return fn

def blob_detect(fp: str, kwargs: dict, r_thr: int = 5, plot: bool = False,
                figsize: Tuple[int, int] = (7, 7), save_dir: str = None) -> str:
    """Detect blobs in an image, .
    
    Args:
        fp: Filepath of image.
        kwargs: Key-word arguments passed to skimage.feature.blob_log.
        r_thr: Remove blobs with radii smaller than this value.
        plot: Plot figures if True.
        figsize: Size of figures to plot.
        save_dir: Directory to save label text files.
    
    Returns:
        The blob coordinates in string format.
    
    """
    img = imread(fp, grayscale=True)        
    h, w = img.shape[:2]
    
    if plot:
        # Draw on the image.
        plt.figure(figsize=figsize)
        plt.imshow(img, cmap='gray')
        plt.title('Image', fontsize=16)
        plt.show()
    
    print(f'Size of image: {w} x {h}.')
    blobs = blob_log(img, **kwargs)
    
    # Add radious in their column.
    blobs[:, 2] = blobs[:, 2] * sqrt(2)
    
    print(f'{len(blobs)} number of blobs detected.')
    
    # Filter the blobs: 
    if plot:   
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
    lines = ''
    
    # Filter blobs.
    blobs = [blob for blob in blobs if blob[2] > r_thr]
    
    print(f'{len(blobs)} number of blobs after radii filtering.')

    for blob in blobs:
        y, x, r = blob.astype(int)
        
        x1, y1 = x - r, y - r
        x2, y2 = x + r, y + r
        
        lines += f'0 {x / w:4f} {y / h:4f} {(x2-x1) / w:4f} {(y2-y1) / h:4f}\n'
        
        if plot:
            img = cv.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 3)
        
    if save_dir is not None:
        # Save the file.
        with open(join(save_dir, f'{get_filename(fp)}.txt'), 'w') as fh:
            fh.write(lines.strip())
        
    if plot:
        plt.figure(figsize=figsize)
        plt.imshow(img, cmap='gray')
        plt.title('Blobs', fontsize=16)
        plt.show()
        
    return lines

