import dash
from dash import Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
from annotationBrowser_panel import annotation_panel
import dash_mantine_components as dmc
from masks import masks_export
tab_layout = dmc.Tabs(
    [
        dmc.TabsList(
            [
                dmc.Tab("Annotation Panel", value="annotationPanel"),
                dmc.Tab("Exported Masks", value="masksExport"),
            ]
        ),
        dmc.TabsPanel(annotation_panel, value="annotationPanel"),
        dmc.TabsPanel(masks_export, value="masksExport"),
    ],
    color="blue",
    orientation="horizontal",
    value="annotationPanel",
)


# Dash app setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div(tab_layout)

## WILL FOR NOW EMBED ALL THE GIRDER_CLIENT LOGIN AND LOGIC IN HERE... SINCE THIS WILL BE SEPARATE FROM THE PANEL ITSELF IN OUR FINAL APP


if __name__ == "__main__":
    app.run_server(debug=True)
