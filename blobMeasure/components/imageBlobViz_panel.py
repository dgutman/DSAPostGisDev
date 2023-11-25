from dash import html, callback, Input, Output, dcc, dash_table
import plotly.graph_objs as go
from skimage import io, measure, draw
import plotly.express as px
from joblib import Memory
from skimage.color import rgb2gray
from skimage.feature import blob_log
import dash_bootstrap_components as dbc
import numpy as np

### Create local cacheing decorator
memory = Memory(".npCacheDir", verbose=0)

sampleImage = "2xtau, CSF1, 15DIV_GREEN.tif"


img = io.imread(sampleImage)


@callback(
    Output(
        "imageROI_data", "data"
    ),  # ID and property of the table where results will be shown
    Input("size-slider", "value"),  # Add other inputs as necessary
    Input("threshold-slider", "value"),
)
@memory.cache
def update_blob_detection(size_value, thresh):
    img = io.imread(sampleImage)
    # If your image is in color, convert it to grayscale
    if len(img.shape) == 3:
        img_gray = rgb2gray(img)
    else:
        img_gray = img

    #    Apply blob detection
    blobs = blob_log(
        img_gray, min_sigma=1, max_sigma=size_value, num_sigma=5, threshold=thresh
    )

    labeled_image = np.zeros_like(img_gray, dtype=np.uint8)

    label = 1
    for blob in blobs:
        y, x, r = blob
        rr, cc = draw.disk((y, x), r, shape=img_gray.shape)
        labeled_image[rr, cc] = label
        label += 1

    # Compute the mean intensity for each blob
    regions = measure.regionprops(labeled_image, intensity_image=img_gray)
    print(regions[1])
    blob_data_for_table = [
        {
            "x": region.centroid[1],
            "y": region.centroid[0],
            "size": region.equivalent_diameter,
            "mean_intensity": region.mean_intensity,
            "blobId": "",
        }
        for region in regions
    ]

    # Return both the raw blob data and the formatted data for the table
    return {"raw_blobs": blobs.tolist(), "table_blobs": blob_data_for_table}


def add_squares_to_figure(image, blobs, color="rgba(255, 0, 0, 0.5)"):
    img = io.imread(sampleImage)
    fig = px.imshow(img)
    fig.update_layout(autosize=True)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False)

    # print(blobs, "Were the blobs received..")
    if blobs:
        for idx, blob in enumerate(blobs):
            y, x, r = blob[:3]
            hovertext = f"Blob ID: {idx}, X: {x}, Y: {y}, Size: {r}"

            fig.add_shape(
                type="rect",
                x0=x - r,
                y0=y - r,
                x1=x + r,
                y1=y + r,
                line=dict(color=color),
                fillcolor=color,
                name=hovertext,
            )

            # Add this inside the for loop in the add_squares_to_figure function
            fig.add_trace(
                go.Scatter(
                    x=[x],
                    y=[y],
                    mode="markers",
                    marker=dict(color="rgba(0,0,0,0)"),  # Invisible marker
                    hoverinfo="text",
                    hovertext=hovertext,
                    name=str(idx),  # Unique name for the callback
                )
            )

    return fig


@callback(
    Output("mainImage_graph", "figure"),
    Input("imageROI_data", "data"),
)
def addROI_boxes(blobData):
    # Use raw blob data to add squares
    raw_blobs = blobData.get("raw_blobs", [])
    ## In future state will read the imageData from a function
    img = io.imread(sampleImage)
    fig = px.imshow(img)
    fig.update_layout(autosize=True)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))

    fig = add_squares_to_figure(fig, raw_blobs, color="rgba(255, 0, 0, 0.5)")
    fig.update_layout(hovermode="closest")

    return fig


blob_detection_controls = dbc.Col(
    [
        html.H4("Blob Detection Controls"),
        dcc.Slider(
            id="size-slider",
            min=0,
            max=100,
            step=1,
            value=50,
            marks={i: str(i) for i in range(0, 101, 10)},
        ),
        dcc.Slider(
            id="threshold-slider",
            min=0,
            max=1,
            step=0.05,
            value=0.1,
            marks={i / 10: "{:.1f}".format(i / 10) for i in range(0, 11)},
        ),
        html.Div(id="hover-data-info"),
        dcc.Store(id="imageROI_data", data={"raw_blobs": [], "table_blobs": []}),
        html.Div(id="roiCount_info"),
        # Add more controls as needed
    ],
    width=3,
)


@callback(Output("hover-data-info", "children"), Input("mainImage_graph", "hoverData"))
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


@callback(
    Output(
        "output-table", "data"
    ),  # ID and property of the table where results will be shown
    Output("roiCount_info", "children"),
    Input("imageROI_data", "data"),  # Add other inputs as necessary
)
def update_ROI_table(data):
    table_data = data.get("table_blobs")
    return table_data, html.Div(
        f"You have detected {len(data['table_blobs'])} blobs on the current main image"
    )


## Note a value > 0.1 basically yields no blobs.. just FYI
### Bind elements based on when the ROI detection generates output


mainImageViz_layout = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(
                figure=px.imshow(img),  ## Seed the graph initially with the base image
                id="mainImage_graph",
                style={"height": "90vh", "width": "100%", "padding": 0, "margin": 0},
                responsive=True,
            ),
            width=8,
        ),
        blob_detection_controls,
    ]
)
