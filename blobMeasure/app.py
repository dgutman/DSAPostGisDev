from dash import Input, Output, State, html, dcc, dash_table
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc


import plotly.graph_objs as go
import json

# from masks import masks_export
from app_config import app
import plotly.express as px
import dash
from skimage import io


from components.imageReg import imageReg_panel

# from components.imageBlobViz_panel import mainImageViz_layout


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

sampleImage = "2xtau, CSF1, 15DIV_GREEN.tif"


tab_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Registration Panel", value="registrationPanel"),
                dmc.Tab("Blob Table", value="blobTable"),
                dmc.Tab("ViewImageStack", value="imageViz"),
            ]
        ),
        dmc.TabsPanel(html.Div("blobo"), value="blobTable"),
        dmc.TabsPanel(html.Div("imageTab"), value="imageViz"),
        dmc.TabsPanel(html.Div(imageReg_panel), "registrationPanel"),
    ],
    color="blue",
    orientation="horizontal",
    value="registrationPanel",
)

# Dash app setup
app.layout = html.Div(tab_layout)
## APP INSTANTIATION OCCURS ON THE APP_CONFIG FILE AS A SINGLETON

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
