"""
Serves the root application layout.
"""
import dash_bootstrap_components as dbc
# from src.components import banner, app_tabs
from dash import Dash, html
from src.components.banner import banner_layout
from src.components.featureDatatable import featureDataTable_layout

app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    banner_layout,
featureDataTable_layout    
])

if __name__ == '__main__':
    app.run(debug=True)