from dash import html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash
import girder_client, os
import numpy as np
from tqdm import tqdm
from PIL import Image
from io import BytesIO
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
from tqdm import tqdm
from dotenv import load_dotenv
from dash import dcc
from argparse import Namespace
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import glob
import torch
import cv2 as cv
from sklearn.model_selection import train_test_split
import yaml
from ultralytics import YOLO
import base64


DSA_BASE_URL = "http://glasslab.neurology.emory.edu:8080/api/v1"
gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
load_dotenv(dotenv_path=".env", override=True)
YoloKEY = os.environ.get("YoloKEY", None)
print("This is the value of the YOLO key", YoloKEY)
if YoloKEY:
    print("This is the API key:", YoloKEY)
    gc.authenticate(apiKey=YoloKEY)

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
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(id="image-display"),
                    ],
                ),
            ]
        ),
    ]
)


##saving the images locally right now, will need to change this
save_dir = "yolo/images"
src_dir_labels = "yolo"
YOLO_OPTIMUS_MODEL = "yolo/models/best.pt"
YOLO_INPUT_TILE_DIR = "yolo/tiles/images/"
IMAGE_SAVE_DIR = "yolo"
predictions_folder = "runs/detect/predict"


# Check or create directories
for p in [
    YOLO_INPUT_TILE_DIR,
    save_dir,
    src_dir_labels,
    IMAGE_SAVE_DIR,
    predictions_folder,
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
        save_dir=save_dir,
        api_url="http://glasslab.neurology.emory.edu:8080/api/v1",
    )
    return args


def get_images(fld_id):
    print(fld_id)
    items = list(gc.listItem(fld_id))
    for item in tqdm(items):
        makedirs(save_dir, exist_ok=True)
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
        imwrite(join(save_dir, f"{get_filename(item['name'])}.png"), img)

        # Get labels
    img_fps = sorted([fp for fp in glob.glob(join(save_dir, "*.png"))])
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


fps = glob.glob(IMAGE_SAVE_DIR + "*.png")


def get_tiles_and_yolo_dataset():
    tiles_dir = join(save_dir, "tiles")
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
    val_txt_fp = join(IMAGE_SAVE_DIR, "val.txt")

    with open(join(IMAGE_SAVE_DIR, "dataset.yaml"), "w") as fh:
        yaml.safe_dump(
            {
                "nc": 1,
                "names": ["nuclei"],
                "path": IMAGE_SAVE_DIR,
                "train": "train.txt",
                "val": "val.txt",
            },
            fh,
        )

    with open(join(IMAGE_SAVE_DIR, "train.txt"), "w") as fh:
        fh.write(
            "\n".join(tiles_df[tiles_df.roi_fp.isin(train_fps)].fp.tolist()).strip()
        )

    with open(join(IMAGE_SAVE_DIR, "val.txt"), "w") as fh:
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
    return images


@callback(Output("image-display", "children"), [Input("image-display", "id")])
def update_images(_):
    images = read_images(predictions_folder)

    # Generate cards for each image
    image_cards = [
        dbc.Col(
            dbc.Card(
                dbc.CardImg(
                    id=f"image-{i}",
                    src=image["image"],
                    top=True,
                    style={"width": "100%", "height": "auto"},
                )
            )
        )
        for i, image in enumerate(images)
    ]

    rows = [dbc.Row(image_cards[i : i + 6]) for i in range(0, len(image_cards), 6)]

    return rows
