from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from annotationBrowser_panel import annotation_panel
import dash_mantine_components as dmc

# from masks import masks_export
from annotationTableView import annotationTable_layout
from app_config import app
from tissueSegModel_panel import tissueSegModel_panel
from yolo import run_yolo

tab_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Annotation Panel", value="annotationPanel"),
                # dmc.Tab("Exported Masks", value="masksExport"),
                dmc.Tab("Annotation Table", value="annotationTable"),
                dmc.Tab("Run Tissue Seg", value="tissueSegModel"),
                dmc.Tab("Yolov8 Results", value="yolo"),
            ]
        ),
        dmc.TabsPanel(annotation_panel, value="annotationPanel"),
        # dmc.TabsPanel(masks_export, value="masksExport"),
        dmc.TabsPanel(annotationTable_layout, value="annotationTable"),
        dmc.TabsPanel(tissueSegModel_panel, value="tissueSegModel"),
        dmc.TabsPanel(run_yolo, value="yolo"),
    ],
    color="blue",
    orientation="horizontal",
    value="annotationPanel",
)

# Dash app setup
app.layout = html.Div(tab_layout)
## APP INSTANTIATION OCCURS ON THE APP_CONFIG FILE AS A SINGLETON

## WILL FOR NOW EMBED ALL THE GIRDER_CLIENT LOGIN AND LOGIC IN HERE... SINCE THIS WILL BE SEPARATE FROM THE PANEL ITSELF IN OUR FINAL APP

server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
