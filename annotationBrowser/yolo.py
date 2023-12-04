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

import plotly.express as px

DSA_BASE_URL = "http://glasslab.neurology.emory.edu:8080/api/v1"
gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
load_dotenv(dotenv_path=".env", override=True)
YoloKEY = os.environ.get("YoloKEY", None)
# print("This is the value of the YOLO key", YoloKEY)
if YoloKEY:
    # print("This is the API key:", YoloKEY)
    gc.authenticate(apiKey=YoloKEY)


##saving the images locally right now, will need to change this
src_dir_images = "yolo/images/"
src_dir_labels = "yolo"
YOLO_OPTIMUS_MODEL = "yolo/models/best.pt"
YOLO_INPUT_TILE_DIR = "yolo/tiles/images/"
SAVE_DIR = "yolo"
predictions_folder = "../runs/detect/predict2"

sampleImage = "yolo/tiles/images/7-27-2023 E20-18 IGHM GFAP-x2880y2880.png"

# Check or create directories
for p in [
    YOLO_INPUT_TILE_DIR,
    src_dir_images,
    src_dir_labels,
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
        fld_id="650887979a8ab9ec771ba678",
        save_dir=src_dir_images,
        api_url="http://glasslab.neurology.emory.edu:8080/api/v1",
    )
    return args


def get_images(fld_id):
    items = list(gc.listItem(fld_id))
    for item in tqdm(items):
        makedirs(src_dir_images, exist_ok=True)
        # Read the metadata to identify the nuclei/DAPI channel.
        channels = item.get("meta", {}).get("Channels", {})
        # Look for nuclei channel.
        channel = None

        for k, v in channels.items():
            if v == "Nuclei":
                channel = k
                break

        # Skip image if no nuclei channel.
        if channel is None:
            continue

        if channel.startswith("Channel"):
            # Special case where channels were not named.
            frame = int(channel[-1]) - 1  # get the frame
        else:
            # Identify the frame that contains nuclei image.
            channel_map = get_tile_metadata(gc, item["_id"]).get("channelmap", {})

            frame = channel_map[channel]

        # Get the image by frame.
        response = gc.get(
            f"item/{item['_id']}/tiles/region?units=base_pixels&exact="
            + f"false&frame={frame}&encoding=PNG",
            jsonResp=False,
        )

        # Save images.
        img = np.array(Image.open(BytesIO(response.content)))
        imwrite(join(src_dir_images, f"{get_filename(item['name'])}.png"), img)

        # Get labels
    img_fps = sorted([fp for fp in glob.glob(join(src_dir_images, "*.png"))])
    if not img_fps:
        print("No PNG files found in the specified directory.")
    else:
        label_dir = join(src_dir_labels, "labels")
        makedirs(label_dir, exist_ok=True)
        print(f"Found {len(img_fps)} PNG files.")
    label_dir = join(src_dir_labels, "labels")
    makedirs(label_dir, exist_ok=True)
    kwargs = {"max_sigma": 30, "num_sigma": 15, "threshold": 0.05}

    for fp in tqdm(img_fps):
        _ = blob_detect(fp, kwargs=kwargs, save_dir=label_dir, plot=False)


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

        imageTileData.append(
            {
                "label": tileRootFile,
                "value": gtt,
                "gtTileImage": os.path.join(truth_tile_dir, gtt),
                "gtLabelFile": gtLabelFile,
            }
        )
    from pprint import pprint

    # pprint(imageTileData)
    return imageTileData


imageNav_controls = dbc.Row(
    [
        dbc.Button(
            "CheckYoloFolders", id="checkResultsFolder_button", style={"width": 300}
        ),
        dcc.Store(id="imageSetList_store", data=[]),
        dcc.Dropdown(
            id="inputImage_select",
            style={"width": 500},
        ),
    ]
)


@callback(
    Output("imageSetList_store", "data"), Input("checkResultsFolder_button", "n_clicks")
)
def updateTileImageList(n_clicks):
    print(n_clicks, "to refresh tile data")
    ## Updating imageSet List store here
    imageSetList = findTruthAndPredictionDataSets(
        YOLO_INPUT_TILE_DIR, predictions_folder
    )
    return imageSetList


## Link the imageSetList store to the dropdown box and also set the default value
@callback(
    Output("inputImage_select", "options"),
    Output("inputImage_select", "value"),
    Input("imageSetList_store", "data"),
)
def updateImageSet_selector(imageSet_data):
    options = [x["label"] for x in imageSet_data]
    value = options[0]
    return options, value


def add_squares_to_figure(imageFigure, blobs, color="rgba(0, 0, 255, 0.5)"):
    # img = io.imread(sampleImage)
    # fig = px.imshow(img)
    # fig.update_layout(autosize=True)
    # fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

    # print(blobs, "Were the blobs received..")
    if blobs:
        for idx, blob in enumerate(blobs):
            # y, x, r = blob[:3]
            hovertext = f"Blob ID: {idx}, X: {blob['x0']}, Y: {blob['y0']}"

            imageFigure.add_shape(
                type="rect",
                x0=blob["x0"] - blob["w"],
                y0=blob["y0"] - blob["h"],
                x1=blob["x0"] + blob["w"],
                y1=blob["y0"] + blob["h"],
                line=dict(color=color),
                fillcolor=color,
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


### Update the image display based on the current displayed image
@callback(
    Output("tile_graph", "figure"),
    Input("inputImage_select", "value"),
    State("imageSetList_store", "data"),
)
def updateMainTileDisplay(selectedTileName, imageSetList):
    # print(selectedTileName)
    if imageSetList:
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
            fig = add_squares_to_figure(fig, labelData)

        fig.update_layout(autosize=True)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

        return fig


#     if selected_option:
#         img = io.imread(tileImagePath)
#         print(img.shape)
#         newFig = px.imshow(img)
#         newFig.update_layout(autosize=True)
#         newFig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

#         return newFig


img = io.imread(sampleImage)
fig = px.imshow(img)
# return fig


def readYoloLabelFile(filename, scaleFactor=1280):
    with open(filename, "r") as file:
        lines = file.readlines()

    headers = ["Label", "x0", "y0", "w", "h"]
    data = []

    for line in lines:
        values = line.strip().split()
        values = [
            float(v) * scaleFactor for v in values
        ]  ## RESCALE FROM 0 to 1 to 0 to tileWidth
        data.append(dict(zip(headers, values)))

    return data


groundTruthEval_panel = dbc.Container(
    [
        imageNav_controls,
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(
                        ## Seed the graph initially with the base image
                        id="tile_graph",
                        figure=fig,
                        responsive=True,
                        style={
                            "height": "90vh",
                            "width": "100%",
                            "padding": 0,
                            "margin": 0,
                        },
                    ),
                    width=6,
                ),
                dbc.Col(html.Div("Graphs Go Here"), width=6),
            ]
        ),
    ]
)


## This is where I will display ground truth results as well as the model results from YOLO Runs
results_viz_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("YoloModelOutputImages", value="yoloResultImages"),
                dmc.Tab("groundTruthChecker", value="checkTruth"),
            ]
        ),
        dmc.TabsPanel(html.Div(id="image-display"), value="yoloResultImages"),
        dmc.TabsPanel(groundTruthEval_panel, value="checkTruth"),
    ],
    color="blue",
    orientation="horizontal",
    value="checkTruth",
)


run_yolo = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "Get Images and Labels",
                            id="get-images-button",
                            className="me-2",
                        )
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Get Tiles and Yolo Dataset",
                            id="get-tiles-button",
                            className="me-2",
                        )
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            "Get Yolo Model Predictions",
                            id="get-yolo-predictions-button",
                            className="me-2",
                        )
                    ],
                    width=2,
                ),
            ]
        ),
        dbc.Row([results_viz_layout]),
    ]
)


@callback(
    Output("get-images-button", "children"),
    Input("get-images-button", "n_clicks"),
)
def update_images(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    args = parse_args()
    get_images(args.fld_id)
    return "Images and Blobs retrieved and saved."


fps = glob.glob(src_dir_images + "*.png")


def get_tiles_and_yolo_dataset():
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

    with open(join(SAVE_DIR, "dataset.yaml"), "w") as fh:
        yaml.safe_dump(
            {
                "nc": 1,
                "names": ["nuclei"],
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
    Output("get-tiles-button", "children"),
    Input("get-tiles-button", "n_clicks"),
)
def update_tiles(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    get_tiles_and_yolo_dataset()
    return "Tiles and Yolo dataset retrieved and saved."


## This is the model trained on optimus
def run_yolo_model():
    model = YOLO(YOLO_OPTIMUS_MODEL)
    results = model.predict(
        YOLO_INPUT_TILE_DIR,
        conf=0.3,
        save_txt=True,
        save_conf=True,
        save=True,
        hide_conf=True,
        hide_labels=True,
    )


@callback(
    Output("get-yolo-predictions-button", "children"),
    Input("get-yolo-predictions-button", "n_clicks"),
)
def update_predictions(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    run_yolo_model()
    return "Predictions retrieved and saved."


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


# @callback(Output("image-display", "children"), [Input("image-display", "id")])
# def update_images(_):
#     images = read_images(predictions_folder)

#     # Generate cards for each image
#     image_cards = [
#         dbc.Col(
#             dbc.Card(
#                 dbc.CardImg(
#                     id=f"image-{i}",
#                     src=image["image"],
#                     top=True,
#                     style={"width": "100%", "height": "auto"},
#                 )
#             )
#         )
#         for i, image in enumerate(images)
#     ]

#     rows = [dbc.Row(image_cards[i : i + 6]) for i in range(0, len(image_cards), 6)]

#     return rows


# from dash import html, callback, Input, Output, dcc, dash_table
# import plotly.graph_objs as go
# from skimage import io, measure, draw
# import plotly.express as px
# from joblib import Memory
# from skimage.color import rgb2gray
# from skimage.feature import blob_log
# import dash_bootstrap_components as dbc
# import numpy as np

# ### Create local cacheing decorator
# memory = Memory(".npCacheDir", verbose=0)


# @callback(
#     Output("tile_graph", "figure"),
#     Input("inputImage_select", "value"),
#     State("imageSetList_store", "data"),
# )
# def updateTileGraph(selectedTile, imageSetList_store):
#     selected_option = next(
#         (item for item in imageSetList_store if item["value"] == selectedTile), None
#     )

#     if selected_option:
#         tileImagePath = selected_option["gtTileImage"]
#         print(tileImagePath, "to be loaded for", selectedTile)
#         img = io.imread(tileImagePath)
#         print(img.shape)
#         newFig = px.imshow(img)
#         newFig.update_layout(autosize=True)
#         newFig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

#         return newFig


# @callback(
#     Output(
#         "imageROI_data", "data"
#     ),  # ID and property of the table where results will be shown
#     Input("size-slider", "value"),  # Add other inputs as necessary
#     Input("threshold-slider", "value"),
# )
# @memory.cache
# def update_blob_detection(size_value, thresh):
#     img = io.imread(sampleImage)
#     # If your image is in color, convert it to grayscale
#     if len(img.shape) == 3:
#         img_gray = rgb2gray(img)
#     else:
#         img_gray = img

#     #    Apply blob detection
#     blobs = blob_log(
#         img_gray, min_sigma=1, max_sigma=size_value, num_sigma=5, threshold=thresh
#     )

#     labeled_image = np.zeros_like(img_gray, dtype=np.uint8)

#     label = 1
#     for blob in blobs:
#         y, x, r = blob
#         rr, cc = draw.disk((y, x), r, shape=img_gray.shape)
#         labeled_image[rr, cc] = label
#         label += 1

#     # Compute the mean intensity for each blob
#     regions = measure.regionprops(labeled_image, intensity_image=img_gray)
#     print(regions[1])
#     blob_data_for_table = [
#         {
#             "x": region.centroid[1],
#             "y": region.centroid[0],
#             "size": region.equivalent_diameter,
#             "mean_intensity": region.mean_intensity,
#             "blobId": "",
#         }
#         for region in regions
#     ]

#     # Return both the raw blob data and the formatted data for the table
#     return {"raw_blobs": blobs.tolist(), "table_blobs": blob_data_for_table}


# def add_squares_to_figure(image, blobs, color="rgba(255, 0, 0, 0.5)"):
#     img = io.imread(sampleImage)
#     fig = px.imshow(img)
#     fig.update_layout(autosize=True)
#     fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

#     # print(blobs, "Were the blobs received..")
#     if blobs:
#         for idx, blob in enumerate(blobs):
#             y, x, r = blob[:3]
#             hovertext = f"Blob ID: {idx}, X: {x}, Y: {y}, Size: {r}"

#             fig.add_shape(
#                 type="rect",
#                 x0=x - r,
#                 y0=y - r,
#                 x1=x + r,
#                 y1=y + r,
#                 line=dict(color=color),
#                 fillcolor=color,
#                 name=hovertext,
#             )

#             # Add this inside the for loop in the add_squares_to_figure function
#             fig.add_trace(
#                 go.Scatter(
#                     x=[x],
#                     y=[y],
#                     mode="markers",
#                     marker=dict(color="rgba(0,0,0,0)"),  # Invisible marker
#                     hoverinfo="text",
#                     hovertext=hovertext,
#                     name=str(idx),  # Unique name for the callback
#                 )
#             )

#     return fig


# @callback(
#     Output("mainImage_graph", "figure"),
#     Input("imageROI_data", "data"),
# )
# def addROI_boxes(blobData):
#     # Use raw blob data to add squares
#     raw_blobs = blobData.get("raw_blobs", [])
#     ## In future state will read the imageData from a function
#     img = io.imread(sampleImage)
#     fig = px.imshow(img)
#     fig.update_layout(autosize=True)
#     fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))

#     fig = add_squares_to_figure(fig, raw_blobs, color="rgba(255, 0, 0, 0.5)")
#     fig.update_layout(hovermode="closest")

#     return fig


# @callback(Output("hover-data-info", "children"), Input("mainImage_graph", "hoverData"))
# def display_hover_data(hoverData):
#     if hoverData is not None:
#         # Extract the relevant hover information
#         # The structure of hoverData depends on how you set up your plot
#         # Typically it's a dictionary where you can find the point's properties
#         hovered_id = hoverData["points"][0][
#             "curveNumber"
#         ]  # or 'pointIndex' or other property
#         return f"Hovered over ROI with ID: {hovered_id}"
#     else:
#         return "Hover over an ROI"


# @callback(
#     Output(
#         "output-table", "rowData"
#     ),  # ID and property of the table where results will be shown
#     Output("roiCount_info", "children"),
#     Input("imageROI_data", "data"),  # Add other inputs as necessary
# )
# def update_ROI_table(data):
#     table_data = data.get("table_blobs")
#     return table_data, html.Div(
#         f"You have detected {len(data['table_blobs'])} blobs on the current main image"
#     )


# ## Note a value > 0.1 basically yields no blobs.. just FYI
# ### Bind elements based on when the ROI detection generates output

# style={
#     "height": "90vh",
#     "width": "100%",
#     "padding": 0,
#     "margin": 0,
# },
# yoloResultViz_controls = dbc.Col(
#     [
#         html.H4("Viz Controls"),
#         dcc.Slider(
#             id="size-slider",
#             min=0,
#             max=100,
#             step=1,
#             value=50,
#             marks={i: str(i) for i in range(0, 101, 10)},
#         ),
#
#         html.Div(id="hover-data-info"),
#         dcc.Store(id="imageROI_data", data={"raw_blobs": [], "table_blobs": []}),
#         html.Div(id="roiCount_info"),
#         # Add more controls as needed
#     ],
#     width=3,
# )
