from dash import html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import girder_client, os
import dash_mantine_components as dmc
import numpy as np
from tqdm import tqdm
from PIL import Image
from io import BytesIO
from skimage import io
import plotly.graph_objects as go
from pprint import pprint
import distinctipy
import dash_ag_grid as dag
from itertools import zip_longest


# from dash import html, callback, Input, Output, dcc, dash_table
# from skimage import io, measure, draw
# import plotly.express as px
# from joblib import Memory
# from skimage.color import rgb2gray
# from skimage.feature import blob_log

# ### Create local cacheing decorator
# memory = Memory(".npCacheDir", verbose=0)


from utils import (
    get_tile_metadata,
    imwrite,
    get_filename,
    blob_detect,
    read_yolo_label,
    im_to_txt_path,
    corners_to_polygon,
    convert_box_type,
    tile_roi_with_labels,
    tile_roi_with_labels_wrapper,
)
from os import makedirs
from os.path import join
from dotenv import load_dotenv
from dash import dcc
from argparse import Namespace
from dash.exceptions import PreventUpdate
import torch
import cv2 as cv
from sklearn.model_selection import train_test_split
import yaml, base64, glob
from ultralytics import YOLO
import dash
from scipy.spatial.distance import dice
import geopandas as gpd
from shapely.geometry import box
import plotly.express as px
import dash_table

from utils import (
    get_tile_metadata,
    imwrite,
    get_filename,
    blob_detect,
    read_yolo_label,
    im_to_txt_path,
    corners_to_polygon,
    convert_box_type,
    tile_roi_with_labels,
    tile_roi_with_labels_wrapper,
)
from os import makedirs
from os.path import join
from dotenv import load_dotenv
from dash import dcc
from argparse import Namespace
from dash.exceptions import PreventUpdate
import torch
import cv2 as cv
from sklearn.model_selection import train_test_split
import yaml, base64, glob
from ultralytics import YOLO
import dash
from scipy.spatial.distance import dice
import geopandas as gpd
from shapely.geometry import box
import plotly.express as px
import dash_table

DSA_BASE_URL = "https://candygram.neurology.emory.edu/api/v1"
gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
load_dotenv(dotenv_path=".env", override=True)
EMKey = os.environ.get("EMKey", None)
# print("This is the value of the YOLO key", YoloKEY)
if EMKey:
    #print("This is the API key:", EMKey)
    gc.authenticate(apiKey=EMKey)

## Exclude the BLUE color we are using for the ground truth..
colorPalette = distinctipy.get_colors(5, exclude_colors=[(0, 0, 1)])
## NEED TO FEED IN THE INITIAL BLUE COLOR I AM USING FOR GROUND TRUTH
## FOR REFERENCE

label_colors = {'0': 'rgba(255, 0, 0, 1)', '1': 'rgba(0, 255, 0, 1)', '2': 'rgba(0, 0, 255, 1)'}

src_dir_images = "emdata/images/"
#src_dir_labels = "emdata"
src_dir = "emdata"
YOLO_OPTIMUS_MODEL = "emdata/models/best.pt"
YOLO_INPUT_TILE_DIR = "emdata/tiles/images/"
SAVE_DIR = "emdata"
predictions_folder = "runs/detect/predict3"

PREDICTION_FOLDER_ROOT = "runs/detect"
#sampleImage = "yolo/tiles/images/7-27-2023 E20-18 IGHM GFAP-x2880y2880.png"

# Check or create directories
for p in [
    YOLO_INPUT_TILE_DIR,
    src_dir,
    #src_dir_images,
    #src_dir_labels,
    SAVE_DIR,
]:
    if not os.path.isdir(p):
        os.makedirs(p, exist_ok=True)


def parse_args():
    """CLI arguments."""
    # Provide default values for the arguments in your Dash app
    args = Namespace(
        user=None,
        password=None,
        fld_id="650ca0d9d3cbdd3f541eb470",
        save_dir=src_dir_images,
        api_url="https://candygram.neurology.emory.edu/api/v1",
    )
    return args

def denote_labels(label):
    if label == 'APOE':
        return 0
    elif label == 'tau filament':
        return 1
    elif label == 'ferritin':
        return 2

def get_em_images(fld_id):
    items = list(gc.listItem(fld_id))
    labels_dir = join(src_dir, "labels")
    makedirs(labels_dir, exist_ok=True)

    images_dir = join(src_dir, "images")  
    makedirs(images_dir, exist_ok=True)
    for item in tqdm(items[:36]):
        response = gc.get(
            f"item/{item['_id']}/tiles/region?units=base_pixels&exact="
            + f"false&encoding=PNG",
            jsonResp=False,
        )
        img = np.array(Image.open(BytesIO(response.content)))
        h,w = img.shape[:2]

        yolo_annotation = ""

        annotations = gc.get(f'annotation/item/{item["_id"]}')
        if not annotations:
            continue
        else:
            for annotation_doc in annotations:
                label = annotation_doc['annotation']['name']
                class_id = denote_labels(label)
                if(class_id == None):
                    continue
                for element in annotation_doc['annotation']['elements']:
                    if element['type'] == 'polyline':

                        points = np.array(element['points'][:4])  
                        x, y = ((max(points[:, 0]) + min(points[:, 0]))/2), ((max(points[:, 1]) + min(points[:, 1]))/2)
                        
                        width = max(points[:, 0]) - min(points[:, 0])
                        height = max(points[:, 1]) - min(points[:, 1])

                        yolo_annotation += f"{class_id} {x / w:.4f} {y / h:.4f} {width / w:.4f} {height / h:.4f}\n"

                    elif element['type'] == 'rectangle':
                        x, y = element['center'][:2]
                        width, height = element['width'], element['height']

                        yolo_annotation += f"{class_id} {x / w:.4f} {y / h:.4f} {width / w:.4f} {height / h:.4f}\n"

        label_filename = f"{get_filename(item['name'])}.txt"
        label_filepath = join(labels_dir, label_filename)
        with open(label_filepath, 'w') as label_file:
            label_file.write(yolo_annotation)
        image_filename = f"{get_filename(item['name'])}.png"
        image_filepath = join(images_dir, image_filename)
        Image.fromarray(img).save(image_filepath)


@callback(
    Output("get-em-images-button", "children"),
    Input("get-em-images-button", "n_clicks"),
)
def update_em_images(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    args = parse_args()
    get_em_images(args.fld_id)
    return "Images and Labels retrieved and saved."


def get_em_tiles_and_yolo_dataset():
    fps = glob.glob(src_dir_images + "*.png")
    tiles_dir = join(SAVE_DIR, "tiles")
    tiles_df = tile_roi_with_labels_wrapper(
        fps,
        tiles_dir,
        tile_size=1280,
        stride=960,
        fill=0,
        notebook=True,
        grayscale=False,
    )
    updated_fps = sorted(fps)
    train_fps, val_fps = train_test_split(updated_fps, train_size=0.8)
    val_txt_fp = join(SAVE_DIR, "val.txt")

    with open(join(SAVE_DIR, "dataset.yaml"), 'w') as fh:
        yaml.safe_dump(
            {
                "nc": 3, 
                "names": ["APOE", "taufilament", "ferritin"], 
                "path": SAVE_DIR, 
                "train": "train.txt",
                "val": "val.txt",
            }, 
            fh,
        )

    with open(join(SAVE_DIR, "train.txt"), "w") as fh:
        fh.write(
            "\n".join(tiles_df[tiles_df.roi_fp.isin(train_fps)].fp.tolist()).strip()
        )

    with open(join(SAVE_DIR, "val.txt"), "w") as fh:
        fh.write("\n".join(tiles_df[tiles_df.roi_fp.isin(val_fps)].fp.tolist()).strip())


@callback(
    Output("get-em-tiles-button", "children"),
    Input("get-em-tiles-button", "n_clicks"),
)
def update_em_tiles(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    get_em_tiles_and_yolo_dataset()
    return "Tiles and Yolo dataset retrieved and saved."

def em_run_yolo_model():
    model = YOLO(YOLO_OPTIMUS_MODEL)
    results = model.predict(
        YOLO_INPUT_TILE_DIR,
        conf=0.2,
        save_txt=True,
        save_conf=True,
        save=True,
        hide_conf=True,
        hide_labels=True,
    )


@callback(
    Output("get-em-yolo-predictions-button", "children"),
    Input("get-em-yolo-predictions-button", "n_clicks"),
)
def update_em_predictions(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    em_run_yolo_model()
    return "Predictions retrieved and saved."

def findTruthAndPredictionDataSets(truth_tile_dir, prediction_tile_root):
    """This will allow us to look at ground truth tiles that have been generated and then see if
    there are also predictions, this makes certain assumptions about the relationship of the labels, but
    I believe this has to be consistent for YOLO to work anyway"""
    groundTruth_tile_set = os.listdir(truth_tile_dir)

    imageTileData = []

    for gtt in groundTruth_tile_set:
        ## Now find the correspond ground Truth labels
        tileRootFile = os.path.basename(gtt).replace(".png", "")
        gtLabelFile = os.path.join(
            truth_tile_dir.replace("images", "labels"), tileRootFile + ".txt"
        )
        if not os.path.isfile(gtLabelFile):
            gtLabelFile = None

        tileYoloPredictions = []
        ## NOW LOOK FOR PREDICTIONS
        yoloPredictOutputDirs = os.listdir(PREDICTION_FOLDER_ROOT)
        for pfldr in yoloPredictOutputDirs:
            curPredictionLabelFile = os.path.join(
                PREDICTION_FOLDER_ROOT, pfldr, "labels", tileRootFile + ".txt"
            )
            if os.path.isfile(curPredictionLabelFile):
                tileYoloPredictions.append(curPredictionLabelFile)


        imageTileData.append(
            {
                "label": tileRootFile,
                "value": gtt,
                "gtTileImage": os.path.join(truth_tile_dir, gtt),
                "gtLabelFile": gtLabelFile,
                "predictedLabelFiles": tileYoloPredictions,
            }
        )
    return imageTileData

imageNav_controls = dbc.Row(
    [
        dbc.Button(
            "CheckYoloFolders", id="em_checkResultsFolder_button", style={"width": 300}
        ),
        dcc.Store(id="em_imageSetList_store", data=[]),
        dcc.Dropdown(
            id="em_inputImage_select",
            style={"width": 500},
        ),
    ]
)

@callback(
    Output("em_imageSetList_store", "data"), Input("em_checkResultsFolder_button", "n_clicks")
)
def updateTileImageList(n_clicks):
    # print(n_clicks, "to refresh tile data")
    ## Updating imageSet List store here
    imageSetList = findTruthAndPredictionDataSets(
        YOLO_INPUT_TILE_DIR, predictions_folder
    )
    return imageSetList


## Link the imageSetList store to the dropdown box and also set the default value
@callback(
    Output("em_inputImage_select", "options"),
    Output("em_inputImage_select", "value"),
    Input("em_imageSetList_store", "data"),
)
def em_updateImageSet_selector(em_imageSet_data):
    options = [x["label"] for x in em_imageSet_data]
    value = options[0]
    return options, value


# def add_squares_to_figure(
#     imageFigure, blobs, color="rgba(0, 0, 255, 1)", fillSquares=False
# ):
    # img = io.imread(sampleImage)
    # fig = px.imshow(img)
    # fig.update_layout(autosize=True)
    # fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

    # print(blobs, "Were the blobs received..")

def add_squares_to_figure(
    imageFigure, blobs, label_colors=None, fillSquares=False
):
    label_colors = label_colors or {}   
    if blobs:
        for idx, blob in enumerate(blobs):
            # y, x, r = blob[:3] 
            hovertext = f"Blob ID: {idx}, X: {blob['x0']}, Y: {blob['y0']}"
            label = blob.get("label", "")
            if label in label_colors:
                color = label_colors[label]
            else:
                color = "rgba(255, 255, 0, 1)"

            imageFigure.add_shape(
                type="rect",
                x0=blob["x0"] - blob["w"],
                y0=blob["y0"] - blob["h"],
                x1=blob["x0"] + blob["w"],
                y1=blob["y0"] + blob["h"],
                line=dict(color=color),
                # fillcolor=color,
                name=hovertext,
            )

            ## TO DO.. ADD The centroid instead of the corner?
            # Add this inside the for loop in the add_squares_to_figure function


            imageFigure.add_trace(
                go.Scatter(
                    x=[blob["x0"]],
                    y=[blob["y0"]],
                    mode="markers",
                    marker=dict(color="rgba(0,0,0,0)"),  # Invisible marker
                    hoverinfo="text",
                    hovertext=hovertext,
                    name=str(idx),  # Unique name for the callback
                )
            )

    return imageFigure

import random


def random_rgb_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return f"rgba({r},{g},{b}, 1)"

### Update the image display based on the current displayed image
@callback(
    Output("em_tile_graph", "figure"),
    Output("em_yolo-object-info", "children"),
    Output("em_dice_coefficient_table", "rowData"),
    Output("em_confusion_matrix_table", "data"),
    Input("em_inputImage_select", "value"),
    State("em_imageSetList_store", "data"),
)
def em_updateMainTileDisplay(selectedTileName, imageSetList):
    dice_coefficient_data_gt = []
    dice_coefficient_data_pred = []
    confusion_matrix_data = []

    if imageSetList:
        yoloObjectDataPanel = []

        selected_option = next(
            (item for item in imageSetList if item["label"] == selectedTileName), None
        )
        tileImagePath = selected_option["gtTileImage"]
        # print(tileImagePath, "to be loaded for", selectedTileName)

        gtLabelFile = selected_option["gtLabelFile"]

        img = io.imread(tileImagePath)
        fig = px.imshow(img)

        annotationData = []
        if gtLabelFile:
            labelData = readYoloLabelFile(gtLabelFile)
            yoloObjectDataPanel.append(
                html.Div(f"Objects in Ground Truth:{len(labelData)}")
            )
            # fig = add_squares_to_figure(fig, labelData)
            fig = add_squares_to_figure(fig, labelData)

        ## NOW SEE IF THERE ARE ANY OTHER RESULTS FILES FROM RUNNING YOLO

        yoloPredictionFiles = selected_option["predictedLabelFiles"]
        if yoloPredictionFiles:
            for idx, ypf in enumerate(yoloPredictionFiles):
                predictedLabelData = readYoloLabelFile(ypf)
                yoloObjectDataPanel.append(
                    html.Div(f"Objects in Predicted Set : {len(predictedLabelData)}")
                )

                # r, g, b = colorPalette[len(colorPalette) % (idx + 1)]
                # roiColor = f"rgba({int(r*255)},{int(g*255)},{int(b*255)},1.0)"
                # fig = add_squares_to_figure(fig, predictedLabelData, color=roiColor)

                fig = add_squares_to_figure(fig, predictedLabelData, label_colors=label_colors)

                dice_coefficient_data_gt.extend(calculate_dice_coefficients(labelData, predictedLabelData))
                dice_coefficient_data_pred.extend(calculate_dice_coefficients(predictedLabelData, labelData))

                true_positives, false_negatives, false_positives = calculate_confusion_matrix(labelData, predictedLabelData)

                confusion_matrix_data.append(
                    {
                        "Metric": "True Positives",
                        "Value": true_positives,
                    }
                )
                confusion_matrix_data.append(
                    {
                        "Metric": "False Negatives",
                        "Value": false_negatives,
                    }
                )
                confusion_matrix_data.append(
                    {
                        "Metric": "False Positives",
                        "Value": false_positives,
                    }
                )

        fig.update_layout(autosize=True)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

        dice_coefficient_data_combined = []
        for gt_data, pred_data in zip_longest(dice_coefficient_data_gt, dice_coefficient_data_pred, fillvalue={}):
            dice_coefficient_data_combined.append({
                "diceCoefficient_gt": gt_data.get("diceCoefficient", None),
                "blobID_gt": gt_data.get("blobID", None),
                "centroidX_gt": gt_data.get("centroidX_gt", None),
                "centroidY_gt": gt_data.get("centroidY_gt", None),
                "centroidX_pred": pred_data.get("centroidX_pred", None),
                "centroidY_pred": pred_data.get("centroidY_pred", None),
                "diceCoefficient_pred": pred_data.get("diceCoefficient", None),
            })

        return fig, yoloObjectDataPanel, dice_coefficient_data_combined, confusion_matrix_data


        # return fig, yoloObjectDataPanel, dice_coefficient_data_gt, dice_coefficient_data_pred, confusion_matrix_data


# img = io.imread(sampleImage)
# fig = px.imshow(img)
# return fig


# def readYoloLabelFile(filename, scaleFactor=1280):
#     with open(filename, "r") as file:
#         lines = file.readlines()

#     headers = ["Label", "x0", "y0", "w", "h"]
#     data = []

#     for line in lines:
#         values = line.strip().split()
#         values = [
#             float(v) * scaleFactor for v in values
#         ]  ## RESCALE FROM 0 to 1 to 0 to tileWidth
#         data.append(dict(zip(headers, values)))

#     return data

def readYoloLabelFile(filename, scaleFactor=1280):
    with open(filename, "r") as file:
        lines = file.readlines()

    headers = ["Label", "x0", "y0", "w", "h"]
    data = []

    for line in lines:
        values = line.strip().split()
        label = values[0]
        values = [float(v) * scaleFactor for v in values[1:]]
        blob_data = dict(zip(headers[1:], values))
        blob_data["label"] = label
        data.append(blob_data)

    return data



dice_table_cols = [
    {"label": "Dice Coefficient (Ground Truth)", "field": "diceCoefficient_gt"},
    {"label": "Dice Coefficient (Prediction)", "field": "diceCoefficient_pred"},
    {"label": "Blob ID (Ground Truth)", "field": "blobID_gt"},
    {"label": "Centroid X (Ground Truth)", "field": "centroidX_gt"},
    {"label": "Centroid Y (Ground Truth)", "field": "centroidY_gt"},
    {"label": "Centroid X (Prediction)", "field": "centroidX_pred"},
    {"label": "Centroid Y (Prediction)", "field": "centroidY_pred"}, 
]

# dice_coefficient_table = dash_table.DataTable(
#     id="dice_coefficient_table",
#     columns=
#     style_table={"height": "1000px", "overflowY": "auto"},
# )

dice_coefficient_table = dag.AgGrid(
    id="em_dice_coefficient_table",
    columnDefs=dice_table_cols,
    style={"overflowY": "auto"},
)

confusion_matrix_table = dash_table.DataTable(
    id="em_confusion_matrix_table",
    columns=[
        {"name": "Metric", "id": "Metric"},
        {"name": "Value", "id": "Value"},
    ],
    style_table={"height": "100px", "overflowY": "auto"},
)

em_groundTruthEval_panel = dbc.Container(
    [
        imageNav_controls,
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        ## Seed the graph initially with the base image
                        id="em_tile_graph",
                        # figure=fig,
                        responsive=True,
                        style={
                            "height": "90vh",
                            "width": "auto",
                            "padding": 0,
                            "margin": 0,
                        },
                    ),
                    width=6,
                    style={"padding-left": 0, "margin-left": 0, "margin-top": 0},
                    className="text-start",
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.Div(id="em_hover-data-info"), width=6),
                                dbc.Col(html.Div(id="em_yolo-object-info"), width=6),
                            ]
                        ),
                        dbc.Row(html.Div(dice_coefficient_table)),
                        dbc.Row(html.Div(confusion_matrix_table)),
                    ],
                    width=6,
                ),
            ]
        ),
    ]
)


em_results_viz_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Yolo Model Output Images", value="em_yoloResultImages"),
                dmc.Tab("groundTruthChecker", value="em_checkTruth"),
            ]
        ),
        dmc.TabsPanel(html.Div(id="em_image-display"), value="em_yoloResultImages"),
        dmc.TabsPanel(em_groundTruthEval_panel, value="em_checkTruth"),
    ],
    color="blue",
    orientation="horizontal",
    value="em_checkTruth",
)

run_yolo_em = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "Get Images and Labels",
                            id="get-em-images-button",
                            className="me-2",
                        )
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Get Tiles and Yolo Dataset",
                            id="get-em-tiles-button",
                            className="me-2",
                        )
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Get Yolo Model Predictions",
                            id="get-em-yolo-predictions-button",
                            className="me-2",
                        )
                    ],
                    width=2,
                ),
            ]
        ),
        dbc.Row([em_results_viz_layout]),
    ]
)

def read_images(folder):
    images = []
    try:
        for filename in os.listdir(folder):
            if filename.endswith(".png"):
                path = os.path.join(folder, filename)
                with open(path, "rb") as f:
                    encoded_image = base64.b64encode(f.read()).decode("utf-8")
                    images.append(
                        {
                            "name": filename,
                            "image": f"data:image/png;base64,{encoded_image}",
                        }
                    )
    except:
        return []
    return images


def calculate_dice_coefficients(selected_ground_truth, predictions):
    dice_coefficient_data = []

    for idx, gt_label in enumerate(selected_ground_truth):
        gt_polygon = box(
            int(gt_label["x0"]),
            int(gt_label["y0"]),
            int(gt_label["x0"] + gt_label["w"]),
            int(gt_label["y0"] + gt_label["h"]),
        )
        max_dice_coefficient = 0
        best_prediction_id = -1

        for prediction_id, prediction_label in enumerate(predictions):
            pred_polygon = box(
                int(prediction_label["x0"]),
                int(prediction_label["y0"]),
                int(prediction_label["x0"] + prediction_label["w"]),
                int(prediction_label["y0"] + prediction_label["h"]),
            )
            intersection_area = gt_polygon.intersection(pred_polygon).area

            gt_area = gt_polygon.area
            pred_area = pred_polygon.area

            dice_coefficient = 2 * intersection_area / (gt_area + pred_area)

            if dice_coefficient > max_dice_coefficient:
                max_dice_coefficient = dice_coefficient
                best_prediction_id = prediction_id

        centroid_x_ground_truth = gt_label["x0"] + gt_label["w"] / 2
        centroid_y_ground_truth = gt_label["y0"] + gt_label["h"] / 2

        if best_prediction_id != -1:
            pred_label = predictions[best_prediction_id]
            centroid_x_pred = pred_label["x0"] + pred_label["w"] / 2
            centroid_y_pred = pred_label["y0"] + pred_label["h"] / 2
            prediction_id = best_prediction_id
        else:
            centroid_x_pred = None
            centroid_y_pred = None
            prediction_id = None

        dice_coefficient_data.append(
            {
                "diceCoefficient": max_dice_coefficient,
                "blobID": prediction_id,
                "centroidX_gt": centroid_x_ground_truth,
                "centroidY_gt": centroid_y_ground_truth,
                "centroidX_pred": centroid_x_pred,
                "centroidY_pred": centroid_y_pred,
            }
        )

    return dice_coefficient_data

def calculate_confusion_matrix(gt_data_set, predictions, threshold=0.25):
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    gt_dice_coefficient_data = calculate_dice_coefficients(gt_data_set, predictions)
    pred_dice_coefficient_data = calculate_dice_coefficients(predictions, gt_data_set)

    for gt_data in gt_dice_coefficient_data:
        dice_coefficient = gt_data["diceCoefficient"]

        if dice_coefficient > threshold:
            true_positives += 1
        else:
            false_negatives += 1

    for pred_data in pred_dice_coefficient_data:
        dice_coefficient = pred_data["diceCoefficient"]

        if dice_coefficient > threshold:
            is_true_positive = any(
                gt_data["diceCoefficient"] > threshold
                for gt_data in gt_dice_coefficient_data
                if gt_data["blobID"] == pred_dice_coefficient_data.index(pred_data)
            )

            if not is_true_positive:
                false_positives += 1
            

    return true_positives, false_negatives, false_positives



@callback(Output("em_hover-data-info", "children"), Input("em_tile_graph", "hoverData"))
def display_hover_data(hoverData):
    if hoverData is not None:
        # Extract the relevant hover information
        # The structure of hoverData depends on how you set up your plot
        # Typically it's a dictionary where you can find the point's properties
        hovered_id = hoverData["points"][0][
            "curveNumber"
        ]  # or 'pointIndex' or other property
        return f"Hovered over ROI with ID: {hovered_id}"
    else:
        return "Hover over an ROI"
