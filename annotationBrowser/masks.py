from dash import html, Output, State, callback, Input
from utils import get_items, get_thumbnail_with_mask
import girder_client, os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import numpy as np
from dash import dcc
import pandas as pd
import dash_bootstrap_components as dbc
import json
from settings import gc

# DSAKEY = os.getenv("DSAKEY")
# DSA_BASE_URL = "https://megabrain.neurology.emory.edu/api/v1"

# gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
# if DSAKEY:
#     gc.authenticate(apiKey=DSAKEY)

## --------------------------------------------------------------------
## WE ARE LINKING THIS PANEL TO THE DATA STORE from the annotaionPanel..


def plot_image_and_mask(img, mask):
    fig_img = px.imshow(img)
    contours = go.Contour(z=mask, showscale=False, colorscale="Viridis", opacity=0.5)
    fig_combined = go.Figure(data=[fig_img.data[0], contours])
    return fig_combined


# masks_export = html.Div(dcc.Graph(figure=fig_combined))
masks_export = dbc.Container(
    [
        html.Div("Mask Export Functionality goes here"),
        dbc.Button("Export Mask", id="exportMaskSet_button"),
        html.Div(id="maskExport_status"),
    ]
)


@callback(
    Output("maskExport_status", "children"),
    Input("exportMaskSet_button", "n_clicks"),
    Input("filteredItem_store", "data"),
)
def exportMaskData(n_clicks, itemData):
    """This will generate a pytorch friendly set of thumbnails, masks, and CSV data for training"""
    ## Probably want to check the dataType of the itemData as well and make sure it's in mask mode..
    if n_clicks and itemData:
        items = itemData["data"]
        ## Just use 1 image for now..
        # items = get_items(gc, "641ba814867536bb7a225533")
        # item = items[0]

        # # item = itemData["data"][0]
        # data = []
        # maskOutputObjects = []
        d = []
        images_folder = "images"
        masks_folder = "masks"
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(masks_folder, exist_ok=True)

        print(len(items), "this is how many docs I have")

        for item in items:
            try:
                # print(f"Processing {item['itemId']}")

                # if 'largeImage' in item:
                #     continue
                # res = item.get("annotation",{}).get("name")
                # if res == "ManualGrayMatter":
                name = item.get("annotation", {}).get("name")

                if name == "ManualGrayMatter":
                    # print("in IF statement", name)
                    # continue
                    img, mask = get_thumbnail_with_mask(
                        gc,
                        # item["_id"],
                        item,
                        512,  # Size to get, if fill not specified then width is prioritized to keep aspect ratio
                        annotation_docs="ManualGrayMatter",  # List of annotation documents or single annotation document
                        annotation_groups=None,  # subset to only a specific list or single annotation group
                        fill=None,  # if this is not None, then the returned images are the exact shape fed in, with this RGB as padding
                        return_contour=False,  # If you want contours returned
                    )

                    img_file_path = os.path.join(
                        images_folder, f'image_{item["itemId"]}.png'
                    )
                    mask_file_path = os.path.join(
                        masks_folder, f'mask_{item["itemId"]}.png'
                    )
                    img_pil = Image.fromarray(img)
                    img_pil.save(img_file_path)

                    mask_pil = Image.fromarray(mask)
                    mask_pil.save(mask_file_path)

                    d.append({"fp": img_file_path, "label": mask_file_path})
            except Exception as e:
                print("Error loading this image")
            # fig_combined = plot_image_and_mask(img, mask)

            # maskOutputObjects.append(dcc.Graph(figure=fig_combined))
        df = pd.DataFrame(d)
        df.to_csv("images_and_mask.csv", index=False)
        # masksOutputObjects.appen
        print("Returning data soon..")
        # return maskOutputObjects
