from dash import html
from utils import get_items, get_thumbnail_with_mask
import girder_client, os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import numpy as np
from dash import dcc

DSAKEY = os.getenv("DSAKEY")
DSA_BASE_URL = "https://megabrain.neurology.emory.edu/api/v1"

gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
if DSAKEY:
    gc.authenticate(apiKey=DSAKEY)

items = get_items(gc, '641ba814867536bb7a225533')

item = items[0]

# Run the function that pulls the image and binary mask drawn from an annotation document.
img, mask = get_thumbnail_with_mask(
    gc, 
    item['_id'], 
    512,  # Size to get, if fill not specified then width is prioritized to keep aspect ratio
    annotation_docs='ManualGrayMatter',  # List of annotation documents or single annotation document
    annotation_groups=None,  # subset to only a specific list or single annotation group
    fill=None,  # if this is not None, then the returned images are the exact shape fed in, with this RGB as padding
    return_contour=False # If you want contours returned
)


def plot_image_and_mask(img, mask):
    fig_img = px.imshow(img)
    contours = go.Contour(z=mask, showscale=False, colorscale="Viridis", opacity=0.5)
    fig_combined = go.Figure(data=[fig_img.data[0], contours])
    return fig_combined
fig_combined = plot_image_and_mask(img, mask)


masks_export = html.Div(dcc.Graph(figure=fig_combined))