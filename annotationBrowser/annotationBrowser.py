import dash
from dash import Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
from annotationBrowser_panel import annotation_panel

# Dash app setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div(annotation_panel)

## WILL FOR NOW EMBED ALL THE GIRDER_CLIENT LOGIN AND LOGIC IN HERE... SINCE THIS WILL BE SEPARATE FROM THE PANEL ITSELF IN OUR FINAL APP


if __name__ == "__main__":
    app.run_server(debug=True)
