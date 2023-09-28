"""
Serves the root application layout.
"""
import dash_bootstrap_components as dbc

# from src.components import banner, app_tabs
from dash import Dash, html
from src.components.banner import banner_layout
from src.components.featureDatatable import featureDataTable_layout
import dash_mantine_components as dmc
from src.components.imageView import imageView_layout


tab_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Cluster Data Table", value="clusterData"),
                dmc.Tab("imageView", value="imageView"),
                dmc.Tab("Feature Confusion Matrix", value="featureConfusionMatrix"),
            ]
        ),
        dmc.TabsPanel(featureDataTable_layout, value="clusterData"),
        dmc.TabsPanel(imageView_layout, value="imageView"),
        dmc.TabsPanel("A confusion matrix goes here", value="featureConfusionMatrix"),
    ],
    color="blue",
    orientation="horizontal",
    value="imageView",
)


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([banner_layout, tab_layout])

if __name__ == "__main__":
    app.run(debug=True)
