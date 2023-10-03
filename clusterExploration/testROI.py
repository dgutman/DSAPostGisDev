import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.graph_objs as go
from PIL import Image
from flask_caching import Cache
import dash_bootstrap_components as dbc

app = dash.Dash(__name__)


cache = Cache(
    app.server, config={"CACHE_TYPE": "filesystem", "CACHE_DIR": ".pointCloudCache"}
)

TIMEOUT = 60000

# Initial position of the rectangle
x0, y0, x1, y1 = 10, 10, 60, 60


def initialize_graph_with_image(baseImage):
    fig = go.Figure()
    img = Image.open("sample_image_for_pointdata.png")
    fig.add_trace(go.Image(z=img))

    fig.update_layout(
        shapes=[
            {
                "type": "rect",
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "line": {"color": "red", "width": 2},
                "xref": "x",
                "yref": "y",
                "layer": "above",
            }
        ]
    )
    return fig


initial_figure = initialize_graph_with_image(
    "demoOne"
)  # Assuming "demoOne" is your default image
# clientside_callback(
#     """
#     function(value, data, figure) {
#         updated_fig = JSON.parse(JSON.stringify(figure))
#         updated_fig['layout']['xaxis]['range'] = [data[value[0]], data[value[1]]]
#         updated_fig['layout']['xaxis]['autorange'] = false
#         return updated_fig
#     }
#     """,
#     Output('fig-id', "figure"),
#     Input("date-slider", "value"),
#     [State("clientside-store-snapshots", "data"), State('fig-id', "figure")],
#     prevent_initial_call=True,
# )

app.layout = html.Div(
    [
        dcc.Store(
            "imageROI_store"
        ),  ## This will keep track of the X, Y, ROI size, and also the numpy array itself
        dcc.Store(id="image-data-store", data=initial_figure["data"]),
        dbc.Select(
            id="baseImage_select", options=["demoOne", "demoTwo"], value="demoOne"
        ),
        dbc.Select(id="roiSize_select", options=[256, 512], value=512),
        dcc.Graph(
            id="image-graph",
            figure={"data": initial_figure["data"], "layout": {}},
            config={
                "staticPlot": False,
                "displayModeBar": False,
                "scrollZoom": False,
                "doubleClick": "reset",
            },
        ),
        html.Div(id="mouse-coordinates"),  # This div will display the mouse coordinates
    ]
)


@app.callback(
    Output("mouse-coordinates", "children"), [Input("image-graph", "hoverData")]
)
def display_mouse_coordinates(hoverData):
    if hoverData and "points" in hoverData and hoverData["points"]:
        x = hoverData["points"][0]["x"]
        y = hoverData["points"][0]["y"]
        return f"Mouse Coordinates: (x: {x}, y: {y})"
    return "Hover over the image to see coordinates"


@app.callback(
    Output("image-graph", "figure"),
    [Input("baseImage_select", "value"), Input("image-graph", "clickData")],
    [State("image-graph", "figure")],
)
def update_graph(baseImage, clickData, current_fig):
    global x0, y0, x1, y1

    # Check if current_fig is None or if it doesn't have expected keys, and initialize it
    if not current_fig or "data" not in current_fig or "layout" not in current_fig:
        current_fig = {"data": [], "layout": {}}

    fig = go.Figure(data=current_fig["data"], layout=current_fig["layout"])

    ctx = dash.callback_context

    # Only update the base image if the dropdown was the triggering input
    if (
        ctx.triggered
        and ctx.triggered[0]["prop_id"].split(".")[0] == "baseImage_select"
    ):
        fig.data = []  # Clear existing data
        img = Image.open("sample_image_for_pointdata.png")
        fig.add_trace(go.Image(z=img))

    # Handle rectangle movement on click
    if clickData:
        print(clickData, "was received...")
        x = clickData["points"][0]["x"]
        y = clickData["points"][0]["y"]

        # Width and height of the rectangle
        width = x1 - x0
        height = y1 - y0

        x0 = x - width / 2
        y0 = y - height / 2
        x1 = x + width / 2
        y1 = y + height / 2
        print(x0, y0, x1, y1, x, y, width, height)
        fig.update_layout(
            shapes=[
                {
                    "type": "rect",
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "line": {"color": "red", "width": 2},
                    "xref": "x",
                    "yref": "y",
                    "layer": "above",
                }
            ]
        )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
