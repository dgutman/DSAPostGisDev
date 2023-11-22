from multiprocessing import Pool
from typing import List, Union, Tuple
from pandas import DataFrame, concat
from typing import Tuple
from pandas import DataFrame
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
import numpy as np
import cv2 as cv

from os import makedirs
from os.path import isfile, join
from os.path import basename, splitext
from typing import Union, Tuple
import numpy as np
import torch

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
        
        tile_df = [job.get() for job in tqdm(jobs)]
        
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


