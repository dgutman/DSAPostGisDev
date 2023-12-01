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
from components.blobTable_layout import blobTable_layout
from components.imageBlobViz_panel import mainImageViz_layout
from components.viewDendraFolder import experimentView_panel

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])


tab_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Registration Panel", value="registrationPanel"),
                dmc.Tab("Blob Table", value="blobTable"),
                dmc.Tab("ViewImageStack", value="imageViz"),
                dmc.Tab("ViewDendraExperiment", value="viewExperiment"),
            ]
        ),
        dmc.TabsPanel(blobTable_layout, value="blobTable"),
        dmc.TabsPanel(mainImageViz_layout, value="imageViz"),
        dmc.TabsPanel(imageReg_panel, "registrationPanel"),
        dmc.TabsPanel(experimentView_panel, "viewExperiment"),
    ],
    color="blue",
    orientation="horizontal",
    value="viewExperiment",
)

# Dash app setup
app.layout = html.Div(tab_layout)
## APP INSTANTIATION OCCURS ON THE APP_CONFIG FILE AS A SINGLETON

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
