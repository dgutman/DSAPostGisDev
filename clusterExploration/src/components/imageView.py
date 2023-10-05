from dash import html, Input, Output, State, dcc, callback
import dash_bootstrap_components as dbc
import pandas as pd
from PIL import Image
import json
import pickle
from ..utils.helpers import load_dataset
import plotly.subplots as sp

mcGraph = dcc.Graph(
    id="multiChannel-graph",
    style={
        "width": "80%",
        "margin": "0px",
        "padding": "0px",
        "display": "inline-block",
        "vertical-align": "top",
    },
    config={
        "staticPlot": False,
        "displayModeBar": True,
        "modeBarButtonsToAdd": ["drawrect"],
    },
)


mcROIgraph = dcc.Graph(
    id="multiChannel-ROI-graph",
    style={
        "width": "80%",
        "margin": "0px",
        "padding": "0px",
        "display": "inline-block",
        "vertical-align": "top",
    },
    config={
        "staticPlot": False,
        "displayModeBar": True,
        # "modeBarButtonsToAdd": ["drawrect"],
    },
)


imageView_layout = html.Div(
    [
        dbc.Select(
            id="imageToRender_select",
            options=["demo", "anotherdemo"],
            style={"maxWidth": 300},
        ),
        html.Span(
            [
                dbc.Select(
                    id="viewportSize_select",
                    options=[256, 512, 768, 1024],
                    value=768,
                    style={"maxWidth": 200},
                ),
            ],
            style={"maxWidth": 300},
        ),
        dbc.Row([html.Div(id="scalingProperties"), dcc.Store("curImageProps_store")]),
        dbc.Row(
            [
                dbc.Col(mcGraph, width=6),
                dbc.Col(
                    [html.Div(id="graph-metadata"), html.Div(id="huh")],
                    width=5,
                ),
                dbc.Col(html.Div(id="mouseTracker"), width=1),
            ]
        ),
    ]
)

sampleCSVFile = "MAP01938_0000_0E_01_region_001_quantification.csv"
data_df = load_dataset(sampleCSVFile)
data = pd.DataFrame(data_df)

### Now let's listen for click events, and for now we will NOT draw an ROI on the image as it
## is taking a weird amount of time, but we will actually generate the zoomed in image and display that


def getImageROI_fromGirder(imageId, startX, startY, roiSize):
    """Returns a numpy array of an image at base resolution at coordinates
    startX, startY of width/height=roiSize"""
    imageUrl = f"item/{imageId}/tiles/region?left={startX}&top={startY}&regionWidth={roiSize}&regionHeight={roiSize}&encoding=pickle"

    try:
        imageData = gc.get(
            imageUrl,
            jsonResp=False,
        )
    except:
        print("Image Data Query failed... DOH")

    imageNP_array = pickle.loads(imageData.content)

    return imageNP_array


## TO BE DEBUGGED
@callback(
    Output("huh", "children"),
    Input("multiChannel-graph", "clickData"),
    Input("curImageProps_store", "data"),
    Input("viewportSize_select", "value"),
)
def renderROI_image(clickData, imageProps, viewportSize):
    if clickData:
        x = clickData["points"][0]["x"]
        y = clickData["points"][0]["y"]

        startX = x * imageProps["scaleFactor"]
        startY = y * imageProps["scaleFactor"]
        region_np = getImageROI_fromGirder(
            imageProps["imageId"], startX, startY, viewportSize
        )
        image_squeezed = np.squeeze(region_np)
        fig = px.imshow(image_squeezed)
        fig = go.Figure(fig)

        min_centroid_x = 250 * imageProps["scaleFactor"]
        max_centroid_x = 450 * imageProps["scaleFactor"]
        min_centroid_y = 3000 * imageProps["scaleFactor"]
        max_centroid_y = 5000 * imageProps["scaleFactor"]
        data_df['x_centroid'] = (data_df['centroid-0'] * imageProps["scaleFactor"]).astype(int)
        data_df['y_centroid'] = (data_df['centroid-1'] * imageProps["scaleFactor"]).astype(int)
        filtered_data = data_df[
            ((data_df['x_centroid'] >= min_centroid_x) & (data_df['x_centroid'] <= max_centroid_x)) &
            ((data_df['y_centroid'] >= min_centroid_y) & (data_df['y_centroid'] <= max_centroid_y))
        ]

        print(data_df.head())

        x_values = filtered_data['x_centroid'].tolist()
        y_values = filtered_data['y_centroid'].tolist()

        x_values_rescaled = [(x - startX) / imageProps["scaleFactor"] for x in x_values]
        y_values_rescaled = [(y - startY) / imageProps["scaleFactor"] for y in y_values]

        ids = [chr(ord('A') + i) for i in range(len(x_values))]

        points = pd.DataFrame({
            "x": x_values_rescaled,
            "y": y_values_rescaled,
            "id": ids
        })

        # points = pd.DataFrame(
        #     {
        #         "x": [50, 100, 150, 200, 250],
        #         "y": [50, 100, 150, 200, 600],
        #         "id": ["A", "B", "C", "D", "E"],
        #     }
        # )

        #Add the scatter plot
        fig.add_trace(
            go.Scatter(
                x=points["x"],
                y=points["y"],
                text=points["id"],
                mode="markers",
                marker=dict(size=10, color="red"),
            )
        )

        fig_dict = fig.to_dict()
        return dcc.Graph(
            figure=fig,
            style={
                "width": "80%",
                "margin": "0px",
                "padding": "0px",
                "display": "inline-block",
                "vertical-align": "top",
            },
            config={
                "staticPlot": False,
                "displayModeBar": True,
                # "modeBarButtonsToAdd": ["drawrect"],
            },
        )


## Let's get a region based on the clicked X y Point...


### This won't do anything yet other than load the only Image I have locally saved...
@callback(
    Output("mouseTracker", "children"), Input("multiChannel-graph", "relayoutData")
)
def trackMousePositionOnMCGraph(relayoutData):
    # print(relayoutData)
    return html.Div(json.dumps(relayoutData))


@callback(
    Output("multiChannel-graph", "figure"),
    Output("curImageProps_store", "data"),
    Input("imageToRender_select", "value"),
)
def loadBaseMultiChannelImage(imageName):
    ## This actually only loads a single image, because I don't have more than one local image to use for this..
    img = Image.open("sample_image_for_pointdata.png")
    width, height = img.size
    fig, tileMetadata = generateMultiVizGraph("demo")

    imageProps = {}

    if imageName == "anotherdemo":
        imageId = "649b3af5fbfabbf55f16e8b1"
        tileData = gc.get(f"item/{imageId}/tiles")
        imageProps = tileData
        imageProps["imageId"] = imageId

        thumbnailWidth = 512

        imageProps["thumbnailWidth"] = 512

        imageProps["scaleFactor"] = imageProps["sizeX"] / thumbnailWidth
        # imageProps["yScaleFactor"] = imageProps["sizeY"] / thumbnailWidth

        ## Retrieve the currently selected image as a numpy array... or an image.. to be determined
        imageThumbnail_data = gc.get(
            f"item/{imageId}/tiles/thumbnail?width={thumbnailWidth}&encoding=pickle",
            jsonResp=False,
        )
        thumb_np = pickle.loads(imageThumbnail_data.content)

        image_squeezed = np.squeeze(thumb_np)

        fig = px.imshow(image_squeezed)
        # Convert the figure to a dictionary
        fig_dict = fig.to_dict()

        return fig_dict, imageProps

    return fig, imageProps


## Bind/display the imageProps dictionary .. for now we can keep it ugly
@callback(Output("scalingProperties", "children"), Input("curImageProps_store", "data"))
def updateCurImageProps(data):
    ## We need to format this and make it prettier, for now I am just dumpign the contents..
    return html.Div(json.dumps(data))


def generateMultiVizGraph(imageName):
    imageMetadata = {}

    #  html.P(f"ScaleFactor X:{image_info['scaleX']}")
    # print("Received", imageName)
    if imageName == "demo":
        img = Image.open("sample_image_for_pointdata.png")
        width, height = img.size
        ## TO DO IS CHANGE THIS IMAGE

        tileMetadata = gc.get(f"item/{imgId}/tiles")

        tileMetadata["scaleX"] = tileMetadata["sizeX"] / width
        tileMetadata["scaleY"] = tileMetadata["sizeY"] / height

        img_array = np.array(img)

        fig = make_subplots(
            rows=1, cols=1, subplot_titles=("Image with Cluster Points",)
        )
        fig.add_trace(go.Image(z=img_array), 1, 1)
        # fig = px.imshow(img_array)
        fig.update_layout(width=800, height=600, margin=dict(t=2, r=2, b=2, l=2))

        # Display image

        fig.update_layout(
            margin=dict(t=6, b=5, l=2, r=2),  # Adjust these values as needed
            dragmode="drawrect",
            shapes=[],
            # dragmode="select",
        )
        fig.update_xaxes(range=[0, width])
        fig.update_yaxes(range=[0, height], scaleanchor="x")

        return fig, tileMetadata

    return None, None


# # Convert the image to a numpy array
# img_array = np.array(img)


# def getImageData(imageName):
#     print("Getting image data for imageName??")

#     if imageName == "demo":
#         # Load the image using PIL
#         # Sample points

#         num_points = len(points)
#         random_colors = [
#             "#%02x%02x%02x" % (int(r), int(g), int(b))
#             for r, g, b in np.random.randint(0, 255, size=(num_points, 3))
#         ]
#         points["color"] = random_colors

#     return imageName


# import dash
# from dash import html, Input, Output, State, dcc, callback
# import dash_bootstrap_components as dbc
# from src.utils.multiChannelHelpers import (
#     generateMultiVizGraph,
#     generateImageMetadataPanel,
# )
# import pandas as pd
# import random

# ## This is the button set to control the graph , this is just a placeholder until I add more
# ## Functionality
# viz_control_layout = html.Div(
#     [
#         dbc.Button(
#             "Graph Random PtSet",
#             id="btn-graph-ptSet",
#             className="me-1",
#             color="success",
#             style={"display": "inline-block"},
#         ),
#         dbc.Button(
#             "Get New PtSet",
#             id="btn-add-random-points",
#             className="me-1",
#             style={"display": "inline-block"},
#         ),
#         dbc.Button(
#             "PlotClusterPts",
#             id="btn-plot-clusterPoints",
#             className="me-1",
#             style={"display": "inline-block"},
#         ),
#     ]
# )


# mcHoverDataGraph = dcc.Graph(
#     id="activeObject-chart",
#     style={
#         "width": "25%",
#         "display": "inline-block",
#         "vertical-align": "top",
#         "margin": "0px",
#         "padding": "0px",
#     },
# )


# mcv_layout = html.Div(
#     [
#         dcc.Store("imageInfo_store"),
#         dcc.Store("graph-data-store"),
#         dcc.Store("activePointList_store"),
#         dbc.Row(viz_control_layout),
#         dbc.Row(
#             [
#                 dbc.Col(id="imageInfo_panel", width=2),
#                 dbc.Col([mcGraph], id="graph_panel", width=8),
#             ]
#         ),
#     ]
# )


# ### Currently using the output from btn-graph-ptSet to initialize the graph


# @callback(Output("imageInfo_panel", "children"), Input("imageInfo_store", "data"))
# def updateImageMetadataPanel(imageMetadata):
#     return generateImageMetadataPanel(imageMetadata)


# @callback(
#     Output("activePointList_store", "data"), Input("btn-plot-clusterPoints", "n_clicks")
# )
# def plotClusterPoints(n_clicks):
#     print("YO")


# # @callback(
# #     [Output("graph-data-store", "data"), Output("imageInfo_store", "data")],
# #     Input("btn-graph-ptSet", "n_clicks"),
# # )
# # def initMainGraph(n_clicks):
# #     graph_layout, imageMetadata = generateMultiVizGraph("demo")
# #     print("Received", imageMetadata)
# #     return graph_layout, imageMetadata


# # @callback(
# #     Output("graph-data-store", "data"),
# #     [Input("btn-add-random-points", "n_clicks")],
# #     [State("graph-data-store", "data")],
# # )
# # def add_random_points(n_clicks, current_figure):
# #     if not n_clicks:
# #         return dash.no_update

# #     # Generate random points (you can modify this as needed)
# #     points = pd.DataFrame(
# #         {
# #             "x": [50, 100, 150, 200, 250],
# #             "y": [50, 100, 150, 200, 600],
# #             "id": ["A", "B", "C", "D", "E"],
# #         }
# #     )

# #     # Add a scatter trace with the random points
# #     new_trace = {
# #         "type": "scatter",
# #         "mode": "markers",
# #         "x": points["x"],
# #         "y": points["y"],
# #         "text": points["id"],
# #         "marker": {"size": 10, "color": "red"},
# #     }

# #     # Append the new trace to the current data
# #     if "data" in current_figure:
# #         current_figure["data"].append(new_trace)
# #     else:
# #         current_figure["data"] = [new_trace]

# #     return current_figure


# # https://github.com/plotly/dash-world-cell-towers
# # @callback(
# #     Output("multiChannel-graph", "figure"),
# #     [Input("graph-data-store", "data")],
# # )
# # def update_graph(data):
# #     return data
# def getPointsToGraph(ptName, minX=100, maxX=500, minY=150, maxY=660, num_points=5):
#     x_values = [random.randint(minX, maxX) for _ in range(num_points)]
#     y_values = [random.randint(minY, maxY) for _ in range(num_points)]
#     ids = ["Pt_" + str(i) for i in range(num_points)]

#     new_points = pd.DataFrame(
#         {
#             "x": x_values,
#             "y": y_values,
#             "id": ids,
#         }
#     )

#     return new_points


# # def getPointsToGraph(ptName, minX=100, maxX=500, minY=150, maxY=660):
# #     new_points = pd.DataFrame(
# #         {
# #             "x": [50, 100, 150, 200, 250],
# #             "y": [50, 100, 150, 200, 600],
# #             "id": ["A", "B", "C", "D", "E"],
# #         }
# #     )


# @callback(
#     [Output("multiChannel-graph", "figure"), Output("imageInfo_store", "data")],
#     [Input("btn-graph-ptSet", "n_clicks"), Input("btn-add-random-points", "n_clicks")],
#     [State("multiChannel-graph", "figure")],
# )
# def update_graph(btn1, btn2, current_figure):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         ## Need this to fire on init so there's something graphed, this will eventually
#         ## get smarted and look for an image as well
#         graph_layout, imageMetadata = generateMultiVizGraph("demo")
#         return graph_layout, imageMetadata
#     else:
#         button_id = ctx.triggered[0]["prop_id"].split(".")[0]

#     if button_id == "btn-graph-ptSet":
#         graph_layout, imageMetadata = generateMultiVizGraph("demo")
#         return graph_layout, imageMetadata

#     elif button_id == "btn-add-random-points":
#         # Generate new points
#         current_figure["data"] = [
#             trace
#             for trace in current_figure["data"]
#             if trace.get("legendgroup") != "random_points"
#         ]

#         new_points = getPointsToGraph("demo")
#         for index, row in new_points.iterrows():
#             current_figure["data"].append(
#                 dict(
#                     x=[row["x"]],
#                     y=[row["y"]],
#                     mode="markers",
#                     marker=dict(color="red", size=10),
#                     hoverinfo="text",
#                     showlegend=False,
#                     legendgroup="random_points"
#                     # text=row["id"],
#                     # name=row["id"],
#                 )
#             )
#         return current_figure, dash.no_update

#     else:
#         return dash.no_update, dash.no_update


### Helper functions to pull and visualize multichannel images from the DSA
from PIL import Image
import numpy as np
import pandas as pd
import urllib
from dash import html
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import girder_client


imgId = "649b7993fbfabbf55f16fba4"
DSA_BaseURL = "https://candygram.neurology.emory.edu/api/v1"

gc = girder_client.GirderClient(apiUrl=DSA_BaseURL)

# encoded_style_value = "%7B%22bands%22:%20%5B%7B%22frame%22:%200,%20%22palette%22:%20%5B%22#000000%22,%20%22#0000ff%22%5D,%20%22min%22:%20%22auto%22,%20%22max%22:%20%22auto%22%7D,%20%7B%22frame%22:%201,%20%22palette%22:%20%5B%22#000000%22,%20%22#00ff00%22%5D,%20%22max%22:%20%22auto%22%7D,%20%7B%22frame%22:%202,%20%22palette%22:%20%5B%22#000000%22,%20%22#ff0000%22%5D,%20%22max%22:%20%22auto%22%7D%5D%7D"

# # Decode the style parameter value
# decoded_style_value = urllib.parse.unquote(encoded_style_value)


points = pd.DataFrame(
    {
        "x": [50, 100, 150, 200, 250],
        "y": [50, 100, 150, 200, 600],
        "id": ["A", "B", "C", "D", "E"],
    }
)


# image_info = {
#     "frames": [
#         {"Frame": 0, "Index": 0},
#         {"Frame": 1, "Index": 1},
#         {"Frame": 2, "Index": 2},
#         {"Frame": 3, "Index": 3},
#         {"Frame": 4, "Index": 4},
#         {"Frame": 5, "Index": 5},
#         {"Frame": 6, "Index": 6},
#         {"Frame": 7, "Index": 7},
#         {"Frame": 8, "Index": 8},
#         {"Frame": 9, "Index": 9},
#         {"Frame": 10, "Index": 10},
#         {"Frame": 11, "Index": 11},
#         {"Frame": 12, "Index": 12},
#         {"Frame": 13, "Index": 13},
#         {"Frame": 14, "Index": 14},
#         {"Frame": 15, "Index": 15},
#         {"Frame": 16, "Index": 16},
#         {"Frame": 17, "Index": 17},
#         {"Frame": 18, "Index": 18},
#         {"Frame": 19, "Index": 19},
#         {"Frame": 20, "Index": 20},
#         {"Frame": 21, "Index": 21},
#         {"Frame": 22, "Index": 22},
#         {"Frame": 23, "Index": 23},
#         {"Frame": 24, "Index": 24},
#         {"Frame": 25, "Index": 25},
#         {"Frame": 26, "Index": 26},
#         {"Frame": 27, "Index": 27},
#     ],
#     "levels": 8,
#     "magnification": None,
#     "mm_x": None,
#     "mm_y": None,
#     "sizeX": 25878,
#     "sizeY": 22220,
#     "tileHeight": 256,
#     "tileWidth": 256,
#     "scaleX": 1.0,
#     "scaleY": 1.0,
# }


def generateImageMetadataPanel(imageMetadata):
    ### Given a dictionary, should generate a formatted panel with the relevant info
    if imageMetadata:
        info_content = html.Div(
            [
                html.H5("Image Information"),
                # html.P(f"Levels: {image_info['levels']}"),
                html.P(f"Size X: {imageMetadata.get('sizeX',{})}"),
                html.P(f"Size Y: {imageMetadata.get('sizeY',{})}"),
                # html.P(f"Tile Height: {image_info['tileHeight']}"),
                # html.P(f"Tile Width: {image_info['tileWidth']}"),
                html.P(f"ScaleFactor X:{imageMetadata['scaleX']:.4f}"),
                html.P(f"ScaleFactor Y:{imageMetadata['scaleY']:.4f}"),
            ],
            style={"margin": "10px"},
        )
        return info_content

    # html.Hr(),
    # html.H6("Frames:"),
    # # html.Ul(
    # #     [
    # #         html.Li(f"Frame: {frame['Frame']}, Index: {frame['Index']}")
    # #         for frame in image_info["frames"]
    # #     ]
    # # ),
