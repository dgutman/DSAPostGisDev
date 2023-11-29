import dash
from dash import Input, Output, State, callback, dcc, html, no_update
import plotly.express as px
import SimpleITK as sitk
from PIL import Image
import numpy as np
import dash_bootstrap_components as dbc
import base64, io
import plotly.graph_objects as go
import cv2
from joblib import Memory


memory = Memory(".npCacheDir", verbose=0)

fixed_image_path = "./assets/2xtau, CSF1, 15DIV_GREEN.tif"
moving_image_path = "./assets/2xtau, CSF1, 17DIV_GREEN.tif"

cardBodyStyle = {
    "padding": "5px",  # Minimize padding but keep some for text
    "textAlign": "center",
}

dataStore_layout = html.Div(
    [
        dcc.Store(id="fixedImage_store", data={"array": ""}),
        dcc.Store(id="movingImage_store", data={"array": ""}),
        dcc.Store(id="registeredImage_store", data={"array": ""}),
        dcc.Store(id="diffImage_store", data={"array": ""}),
        dcc.Store(id="xfm_store", data={"array": ""}),
    ]
)


homography_descr_markdown = """
```
H = | h00 h01 h02 |
    | h10 h11 h12 |
    | h20 h21 h22 |
```


**Mapping:**
- Maps a point (x, y) from the source image to a point (x', y') in the destination image using homogeneous coordinates.
- (x', y', w') = H * (x, y, 1)
- Cartesian coordinates: x' = x'/w', y' = y'/w'

**Matrix Elements:**
- h00, h01, h10, h11: Control scaling, rotation, and shearing.
- h02, h12: Represent translations in x and y directions.
- h20, h21, h22: Handle perspective transformations. h22 is usually 1.


"""


homography_info = dbc.Card(
    [
        dbc.CardHeader("Homography Matrix Explanation"),
        dbc.CardBody([dcc.Markdown(homography_descr_markdown)]),
    ]
)


def resampleArrayImage(image_as_np, sampleFactor=4):
    ## Given a numpy array that is an image, downSample by a given factor
    # Assuming 'image_np' is your numpy array
    image_pil = Image.fromarray(image_as_np)

    # Calculate new dimensions
    new_width = image_pil.width // 4
    new_height = image_pil.height // 4

    # Downsample the image
    resized_image_pil = image_pil.resize((new_width, new_height))

    # Convert back to numpy array if needed
    resized_image_np = np.array(resized_image_pil)
    return resized_image_np


imageReg_Controls = dbc.Row(
    [
        dbc.Col(
            dbc.Button(
                "RunImageReg",
                id="runImageReg",
                style={"width": "150px", "margin": "20px"},
            ),
            width=2,
        ),
        dbc.Col(
            dcc.Slider(
                id="diffImage_slider",
                min=0,
                max=100,
                value=10,
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Switch(
                id="showHistogram-switch",
                label="Generate Histograms",
                value=False,
            ),
            width=2,
        ),
        dbc.Col(
            dbc.Switch(
                id="invertResigteredColors-switch",
                label="Invert Reg Colors",
                value=True,
            ),
            width=2,
        ),
    ]
)

imageReg_panel = dbc.Container(
    [
        dataStore_layout,
        imageReg_Controls,
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                "FIXED", className="card-text", style=cardBodyStyle
                            ),
                            dcc.Graph(
                                id="fixedImage",
                            ),
                        ],
                        color="primary",
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                "Moving", className="card-text", style=cardBodyStyle
                            ),
                            dcc.Graph(id="movingImage"),
                        ],
                        color="primary",
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                "Registration",
                                className="card-text",
                                style=cardBodyStyle,
                            ),
                            dcc.Graph(id="registeredImage"),
                        ],
                        color="primary",
                        style={"margin": 0, "padding": 0},
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                "DIFF",
                                className="card-text",
                                style=cardBodyStyle,
                            ),
                            dcc.Graph(id="diffImage"),
                        ],
                        color="primary",
                        style={"margin": 0, "padding": 0},
                    ),
                    width=3,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Card(id="currentXfm"), width=8),
                dbc.Col(homography_info, width=4),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                "FIXED Hist", className="card-text", style=cardBodyStyle
                            ),
                            dcc.Graph(
                                id="fixedImage_hist",
                            ),
                        ],
                        color="primary",
                        style={"display": "none"},
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                "Moving Hist",
                                className="card-text",
                                style=cardBodyStyle,
                            ),
                            dcc.Graph(id="movingImage_hist"),
                        ],
                        color="primary",
                        style={"display": "none"},
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dcc.Graph(id="registeredImage_hist"),
                            dbc.CardBody(
                                "Registration Hist",
                                className="card-text",
                                style=cardBodyStyle,
                            ),
                        ],
                        color="primary",
                        style={"margin": 0, "padding": 0, "display": "none"},
                    ),
                    width=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                "DIFF Hist",
                                className="card-text",
                                style=cardBodyStyle,
                            ),
                            dcc.Graph(id="diffImage_hist"),
                        ],
                        color="primary",
                        style={"margin": 0, "padding": 0, "display": "none"},
                    ),
                    width=3,
                ),
            ]
        ),
    ],
)

import json


def format_matrix(matrix):
    return "\n".join(["\t".join([f"{item:.4f}" for item in row]) for row in matrix])


@callback(Output("currentXfm", "children"), Input("xfm_store", "data"))
def displayCurrentXfmCards(currentXfmdata):
    formatted_xfm = format_matrix(currentXfmdata["xfm"])
    formatted_inv_xfm = format_matrix(currentXfmdata["inv_xfm"])

    xfm_layout = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Forward Transformation Matrix"),
                        dbc.CardBody([dcc.Markdown(f"```\n{formatted_xfm}\n```")]),
                    ]
                ),
                width=4,
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Inverse Transformation Matrix"),
                        dbc.CardBody([dcc.Markdown(f"```\n{formatted_inv_xfm}\n```")]),
                    ]
                ),
                width=4,
            ),
        ]
    )

    return xfm_layout


### Sycnhronize the ZOOM between the 1st, 3rd and 4th windows, maybe also put a box on the second image
@callback(
    Output("registeredImage", "figure"),
    Output("diffImage", "figure"),
    Input("fixedImage", "relayoutData"),
    Input("registeredImage_store", "data"),
    Input("invertResigteredColors-switch", "value"),
    State("fixedImage_store", "data"),
)
def sync_zoom(relayoutData, regImage_data, invertRegColors, fixedImage_data):
    ctx = dash.callback_context

    ## TO DEBUG.. APPEARS MORE THAN ONE CALLBACK CAN UPDATE THe CALL BACK
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    ### Get the data for the registered image...
    encoded_registeredImage = regImage_data["array"]
    if encoded_registeredImage:
        buffer = io.BytesIO(base64.b64decode(encoded_registeredImage))
        registered_image_np = np.load(buffer)

        if invertRegColors:
            ## Invert colors
            image_color_flipped = registered_image_np.copy()
            image_color_flipped[:, :, 1], image_color_flipped[:, :, 2] = (
                registered_image_np[:, :, 2],
                registered_image_np[:, :, 1],
            )
            registered_image_np = image_color_flipped

        # registered_image_np = registered_image_np[registered_image_np < thresh]
        registered_fig = px.imshow(registered_image_np)
        registered_fig.update_layout(autosize=True)
        registered_fig.update_layout(margin=dict(l=0, r=4, t=0, b=0), showlegend=False)

        encoded_fixedData = fixedImage_data["array"]
        # Your code here

        # if encoded_fixedData and encoded_registeredImage:
        buffer = io.BytesIO(base64.b64decode(encoded_fixedData))
        fixed_image_np = np.load(buffer)

        difference_fig = generateDiffImage_figure(fixed_image_np, registered_image_np)
        ## Now generate the DIFF image data

        # Check if zoom event (like drag or zoom) occurred
        if "xaxis.range[0]" in relayoutData and "yaxis.range[0]" in relayoutData:
            x_range = [relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]]
            y_range = [relayoutData["yaxis.range[0]"], relayoutData["yaxis.range[1]"]]

            # # Update the xaxis and yaxis range of the other figures
            registered_fig["layout"]["xaxis"]["range"] = x_range
            registered_fig["layout"]["yaxis"]["range"] = y_range

            difference_fig["layout"]["xaxis"]["range"] = x_range
            difference_fig["layout"]["yaxis"]["range"] = y_range

        return registered_fig, difference_fig
    raise dash.exceptions.PreventUpdate


def generateDiffImage_figure(np_fixedImage, np_registeredImage):
    # Convert the images to grayscale
    fixed_image_gray = cv2.cvtColor(np_fixedImage, cv2.COLOR_BGR2GRAY)
    registered_image_gray = cv2.cvtColor(np_registeredImage, cv2.COLOR_BGR2GRAY)

    # Convert to a signed data type for subtraction
    fixed_image_signed = fixed_image_gray.astype(np.int16)
    registered_image_signed = registered_image_gray.astype(np.int16)

    # Subtract the images
    difference = fixed_image_signed - registered_image_signed

    # Create an empty image for visualization (with 3 channels for RGB)
    new_image = np.zeros((*difference.shape, 3), dtype=np.uint8)

    # Positive differences (red channel)
    positive_diff = np.clip(difference, 0, None)
    positive_diff_scaled = (255 * (positive_diff / np.max(positive_diff))).astype(
        np.uint8
    )
    new_image[:, :, 0] = positive_diff_scaled

    # Negative differences (blue channel)
    negative_diff = np.clip(-difference, 0, None)
    negative_diff_scaled = (255 * (negative_diff / np.max(negative_diff))).astype(
        np.uint8
    )
    new_image[:, :, 2] = negative_diff_scaled

    # Generate the figure
    difference_fig = px.imshow(new_image)
    difference_fig.update_layout(autosize=True)
    difference_fig.update_layout(margin=dict(l=0, r=4, t=0, b=0), showlegend=False)
    return difference_fig


# @memory.cache
def register_images_ver2(fixed_image, moving_image):
    # Load images
    # fixed_image = cv2.imread(fixed_image)  # 0 for grayscale
    # moving_image = cv2.imread(moving_image)

    # Detect features and compute descriptors.
    sift = cv2.SIFT_create()
    keypoints_1, descriptors_1 = sift.detectAndCompute(fixed_image, None)
    keypoints_2, descriptors_2 = sift.detectAndCompute(moving_image, None)

    # Feature matching
    matcher = cv2.BFMatcher()
    matches = matcher.knnMatch(descriptors_1, descriptors_2, k=2)

    # Apply ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    # Extract location of good matches
    points1 = np.float32([keypoints_1[m.queryIdx].pt for m in good_matches]).reshape(
        -1, 1, 2
    )
    points2 = np.float32([keypoints_2[m.trainIdx].pt for m in good_matches]).reshape(
        -1, 1, 2
    )

    # Find homography
    homography, mask = cv2.findHomography(points1, points2, cv2.RANSAC)

    ## NEED TO INVERT THE HOMOGRAPH AS WELL
    inv_homography = np.linalg.inv(homography)

    # Warp image
    height, width, _ = fixed_image.shape
    aligned_image = cv2.warpPerspective(moving_image, inv_homography, (width, height))

    return aligned_image, {"xfm": homography, "inv_xfm": inv_homography}


@callback(Output("fixedImage_store", "data"), Input("runImageReg", "n_clicks"))
def loadFixedImage(n_clicks):
    fixed_image_np = np.array(Image.open(fixed_image_path))

    fixed_image_np = resampleArrayImage(fixed_image_np)

    # Convert array to a byte stream and then to a base64 string
    buffer = io.BytesIO()
    np.save(buffer, fixed_image_np)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {"array": encoded}


### Load the moving Image into a dcc.Store
@callback(Output("movingImage_store", "data"), Input("runImageReg", "n_clicks"))
def loadMovingImage(n_clicks):
    fixed_image_np = np.array(Image.open(moving_image_path))

    fixed_image_np = resampleArrayImage(fixed_image_np)

    # Convert array to a byte stream and then to a base64 string
    buffer = io.BytesIO()
    np.save(buffer, fixed_image_np)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return {"array": encoded}


def generateImageHistogram(np_imageData, imageLabel=None):
    """This expects the data to be an numpy array, and generates a histogram
    Will add an option to generate grayscale or color in the next iteration"""
    ## Maybe detect the type in a future version to make this less annoying
    image = np_imageData

    blue, green, red = image[:, :, 0], image[:, :, 1], image[:, :, 2]

    # Create a figure with subplots
    fig = go.Figure()

    # Add a histogram for each color channel
    fig.add_trace(
        go.Histogram(x=red.flatten(), name="Red", marker_color="red", nbinsx=256)
    )
    fig.add_trace(
        go.Histogram(x=green.flatten(), name="Green", marker_color="green", nbinsx=256)
    )
    fig.add_trace(
        go.Histogram(x=blue.flatten(), name="Blue", marker_color="blue", nbinsx=256)
    )

    # Update the layout
    fig.update_layout(
        title=f"{imageLabel} Color Image Histogram",
        xaxis_title="Pixel Intensity",
        yaxis_title="Count",
        yaxis_type="log",
    )
    return fig


### Generate histogram for the fixed
@callback(
    Output("fixedImage_hist", "figure"),
    Input("fixedImage_store", "data"),
    Input("showHistogram-switch", "value"),
)
def generateFixedImageHistogram(fixedImage_data, genHistogram):
    if genHistogram:
        # Assuming 'data' is retrieved from dcc.Store
        encoded = fixedImage_data["array"]

        buffer = io.BytesIO(base64.b64decode(encoded))
        image = np.load(buffer)

        return generateImageHistogram(image, "Fixed")


### Generate histogram for the movingImage
@callback(
    Output("movingImage_hist", "figure"),
    Input("movingImage_store", "data"),
    Input("showHistogram-switch", "value"),
)
def generateMovingImageHistogram(movingImage_data, genHistogram):
    if genHistogram:
        # print("Trying to generate moving image histogram...")

        # Assuming 'data' is retrieved from dcc.Store
        encoded = movingImage_data["array"]
        buffer = io.BytesIO(base64.b64decode(encoded))
        image = np.load(buffer)

        return generateImageHistogram(image, "Moving")


### Generate histogram for the movingImage
@callback(
    Output("registeredImage_hist", "figure"),
    Input("registeredImage_store", "data"),
    Input("showHistogram-switch", "value"),
)
# @memory.cache
def generateRegistationHistogram(movingImage_data, genHistogram):
    if genHistogram:
        print("Trying to generate registration image histogram...")

        # Assuming 'data' is retrieved from dcc.Store
        encoded = movingImage_data["array"]

        if encoded:
            buffer = io.BytesIO(base64.b64decode(encoded))
            image = np.load(buffer)

            return generateImageHistogram(image, "Registered")


@callback(Output("fixedImage", "figure"), Input("fixedImage_store", "data"))
def renderFixedImage(fixedImage_data):
    # Assuming 'data' is retrieved from dcc.Store
    encoded = fixedImage_data["array"]

    if encoded:
        buffer = io.BytesIO(base64.b64decode(encoded))
        fixed_image_np = np.load(buffer)
        fixed_fig = px.imshow(fixed_image_np)
        fixed_fig.update_layout(autosize=True)
        fixed_fig.update_layout(margin=dict(l=0, r=4, t=0, b=0), showlegend=False)

        return fixed_fig

    return None


@callback(Output("movingImage", "figure"), Input("movingImage_store", "data"))
def renderMovingImage(movingImage_data):
    # Assuming 'data' is retrieved from dcc.Store
    encoded = movingImage_data["array"]

    if encoded:
        buffer = io.BytesIO(base64.b64decode(encoded))
        moving_image_np = np.load(buffer)
        moving_fig = px.imshow(moving_image_np)
        moving_fig.update_layout(autosize=True)
        moving_fig.update_layout(margin=dict(l=0, r=4, t=0, b=0), showlegend=False)

        return moving_fig

    return None


# @callback(
#     Output("registeredImage", "figure"),
#     Input("registeredImage_store", "data"),
#     Input("diffImage_slider", "value"),
# )
# def renderRegisteredImage(reg_data, thresh):
#     encoded = reg_data["array"]
#     print("Trying to output registered image store", len(encoded))
#     if encoded:
#         buffer = io.BytesIO(base64.b64decode(encoded))

#         registered_image_np = np.load(buffer)

#         # registered_image_np = registered_image_np[registered_image_np < thresh]

#         registered_fig = px.imshow(registered_image_np)
#         registered_fig.update_layout(autosize=True)
#         registered_fig.update_layout(margin=dict(l=0, r=4, t=0, b=0), showlegend=False)

#         return registered_fig
#     return None


@callback(
    Output("registeredImage_store", "data"),
    Output("xfm_store", "data"),
    Input("runImageReg", "n_clicks"),
)
def load_fixedMoving_image(init_panel_clicked):
    ## This will be replaced at some point by a dropdown that selects a case..

    moving_image_np = np.array(Image.open(moving_image_path))
    fixed_image_np = np.array(Image.open(fixed_image_path))

    moving_image_np = resampleArrayImage(moving_image_np)
    fixed_image_np = resampleArrayImage(fixed_image_np)

    aligned_image, xfm_data = register_images_ver2(fixed_image_np, moving_image_np)
    ## ADD A PARAM TO INVERT OR FLIP COLORS..
    # print(aligned_image.shape, "is the shape of the aligned image")
    buffer = io.BytesIO()
    np.save(buffer, aligned_image)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    # print(aligned_image.shape)

    ## Invert colors
    moving_image_red = aligned_image.copy()
    moving_image_red[:, :, 1], moving_image_red[:, :, 2] = (
        aligned_image[:, :, 2],
        aligned_image[:, :, 1],
    )

    # # Convert to a signed data type
    # fixed_image_signed = fixed_image_np.astype(np.int16)
    # aligned_image_signed = aligned_image.astype(np.int16)

    # # Subtract the images
    # difference_image = aligned_image_signed - fixed_image_signed

    # print(max(difference_image))

    # # Create an empty color image (3 channels for RGB)
    # diff_min = np.min(difference_image)
    # diff_max = np.max(difference_image)

    # # print(diff_min, diff_max)
    # if diff_max - diff_min != 0:
    #     scaled_difference = 255 * (difference_image - diff_min) / (diff_max - diff_min)
    #     scaled_difference = scaled_difference.astype(np.uint8)
    # else:
    #     # Handle the case where all values in difference_image are the same
    #     scaled_difference = np.zeros_like(difference_image, dtype=np.uint8)

    # # Create a visualization array with the correct shape
    # visualization = np.zeros(
    #     (difference_image.shape[0], difference_image.shape[1], 3), dtype=np.uint8
    # )

    # # Update red channel for positive differences
    # visualization[:, :, 0] = np.where(
    #     difference_image[:, :, 0] > 0, scaled_difference[:, :, 0], 0
    # )

    # # Update blue channel for negative differences
    # visualization[:, :, 2] = np.where(
    #     difference_image[:, :, 0] < 0, scaled_difference[:, :, 0], 0
    # )

    # # Assign intensity to the red/blue channel based on the difference
    # visualization[:, :, 0] = np.where(
    #     difference_image > 0, scaled_difference, 0
    # )  # Red for positive differences
    # visualization[:, :, 2] = np.where(
    #     difference_image < 0, scaled_difference, 0
    # )  # Blue for negative differences

    # # Assign intensity to the red/blue channel based on the difference

    # Check if visualization array is in the expected shape
    # if visualization.ndim == 3 and visualization.shape[2] == 3:
    #     diff_fig = px.imshow(visualization)
    #     diff_fig.update_layout(autosize=True)
    #     diff_fig.update_layout(margin=dict(l=0, r=4, t=0, b=0), showlegend=False)
    # else:
    #     print(visualization.shape)
    #     diff_fig = go.Figure()  # Or handle the empty case in another way

    # diff_hist = generateImageHistogram(visualization, "Diff Image")

    return {"array": encoded}, xfm_data
