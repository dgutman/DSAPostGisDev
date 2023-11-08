import sys
from dash import html, Input, Output, State, callback
from settings import gc
from dbHelpers import generate_generic_DataTable
import pandas as pd
import dash_bootstrap_components as dbc
from dataView_component import getImageThumb_as_NP, plotImageAnnotations
from models import uNetResNet
import torch
import cv2 as cv
import dash_core_components as dcc
import plotly.graph_objs as go
import numpy as np
from models import val_transforms
from models import uNet
sampleFolderId = "645b9e006df8ba8751a909dd"


itemList = list(gc.listItem(sampleFolderId))


df = pd.DataFrame(itemList)
col_defs = [{"field": "_id"}, {"field": "name"}]


tissueSegModel_panel = html.Div(
    [
        generate_generic_DataTable(df, "sampleImageList_table", col_defs),
        # html.Div(id="modelOutput_div"),
        # html.Div(id="tissueOutput_div"),
        dbc.Row(
            [
                dbc.Col(html.Div(id="modelOutput_div")),
                dbc.Col(html.Div(id="tissueOutput_div")),
            ]
        ),
    ]
)

model = uNetResNet(in_channels=3, out_channels=1,pretrained=True) 
model.load_state_dict(
      torch.load('best.pt', 
                  map_location=torch.device('cpu'))
   )
model.eval()

tissueSeg_model = uNet(in_channels=3,out_channels=1)
tissueSeg_model.load_state_dict(
      torch.load('tissueModelbest.pt', 
                  map_location=torch.device('cpu'))
   )
tissueSeg_model.eval()

def reshape_with_pad(img, size, pad = (255, 255, 255)):
    """Reshape an image into a square aspect ratio without changing the original
    image aspect ratio - i.e. use padding.
    
    """
    h, w = img.shape[:2]

    if w > h:
        img = cv.copyMakeBorder(img, 0, w-h, 0, 0, cv.BORDER_CONSTANT, None, 
                                pad)
    else:
        img = cv.copyMakeBorder(img, 0, 0, 0, h-w, cv.BORDER_CONSTANT, None, 
                                pad)

    # Reshape the image.
    img = cv.resize(img, (size, size), None, None, cv.INTER_NEAREST)

    return img

@callback(
    Output("modelOutput_div", "children"),
    Input("sampleImageList_table", "selectedRows"),
)
def selected(selected):
    if selected:
        imageId = selected[0]["_id"]

        #        image_as_np = getImageThumb_as_NP(selected[0]["_id"])

        #image_fig = plotImageAnnotations(imageId)
        image_copy= getImageThumb_as_NP(imageId)
        image_with_contours = image_copy.copy()
        orig_shape = (image_copy.shape[1], image_copy.shape[0])
        image_copy = image_copy[:, :, :3]
        image = val_transforms(image_copy)
        with torch.set_grad_enabled(False):
            image = image.unsqueeze(0)
            pred = model(image)
        pred = (pred[0][0] > 0.5).data.cpu().numpy()
        pred = pred.astype(np.uint8) * 255
        pred = cv.resize(pred, (orig_shape[0], orig_shape[1]), interpolation=cv.INTER_NEAREST)
        contours, hierarchy  = cv.findContours(pred, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        cv.drawContours(image_with_contours, contours, -1, (0, 0, 255), 2)
        image_with_contours_trace = go.Image(z=image_with_contours)


        layout = go.Layout(
            #title=selected[0]["name"],
            title = "Gray Matter Model",
            showlegend=False
        )
        fig = go.Figure(data=[image_with_contours_trace], layout=layout)

        return dbc.Container([
            # dbc.Row([
            #     dbc.Col(html.Div(selected[0]["name"]))
            # ]),
            dbc.Row([
                #dbc.Col(image_fig), 
                dbc.Col(dcc.Graph(figure=fig))
            ])
        ])


@callback(
    Output("tissueOutput_div", "children"),
    Input("sampleImageList_table", "selectedRows"),
)
def selected(selected):
    if selected:
        imageId = selected[0]["_id"]

        #        image_as_np = getImageThumb_as_NP(selected[0]["_id"])

        #image_fig = plotImageAnnotations(imageId)
        image_copy= getImageThumb_as_NP(imageId)
        image_with_contours = image_copy.copy()
        orig_shape = (image_copy.shape[1], image_copy.shape[0])
        image_copy = image_copy[:, :, :3]
        image = val_transforms(image_copy)
        with torch.set_grad_enabled(False):
            image = image.unsqueeze(0)
            pred = tissueSeg_model(image)
        pred = (pred[0][0] > 0.5).data.cpu().numpy()
        pred = pred.astype(np.uint8) * 255
        pred = cv.resize(pred, (orig_shape[0], orig_shape[1]), interpolation=cv.INTER_NEAREST)
        contours, hierarchy  = cv.findContours(pred, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        #epsilon = 0.002 * cv.arcLength(contours[0], True)  
        #smoothed_contours = [cv.approxPolyDP(cnt, epsilon, True) for cnt in contours]
        #image_trace = go.Image(z=image_copy)
        #mask_trace = go.Contour(z=pred, showscale=False, contours=dict(showlines=False))
        cv.drawContours(image_with_contours, contours, -1, (0, 0, 255), 2)
        image_with_contours_trace = go.Image(z=image_with_contours)
        # smoothed_contours_trace = go.Scatter(
        #     x=[point[0] for point in smoothed_contours[0][:, 0, 0]],
        #     y=[point[0] for point in smoothed_contours[0][:, 0, 1]],
        #     mode='lines',
        #     line=dict(color='red', width=2)
        # )

        layout = go.Layout(
            #title=selected[0]["name"],
            title = "Tissue Detector Model",
            showlegend=False
        )

        #fig = go.Figure(data=[image_trace, mask_trace], layout=layout)
        fig = go.Figure(data=[image_with_contours_trace], layout=layout)

        return dbc.Container([
            # dbc.Row([
            #     dbc.Col(html.Div(selected[0]["name"]))
            # ]),
            dbc.Row([
                #dbc.Col(image_fig), 
                dbc.Col(dcc.Graph(figure=fig))
            ])
        ])



