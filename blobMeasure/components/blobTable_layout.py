from dash import html, dash_table
import dash_bootstrap_components as dbc


results_table = dbc.Col(
    dash_table.DataTable(
        id="output-table",
        columns=[{"name": i, "id": i} for i in ["x", "y", "size", "mean_intensity"]],
        data=[],
    ),
    width=12,
)


blobTable_layout = html.Div([results_table])
