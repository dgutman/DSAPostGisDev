from dash import html, dash_table
import dash_bootstrap_components as dbc
import dash_ag_grid as dag


results_table = dbc.Col(
    dag.AgGrid(
        id="output-table",
        columnDefs=[
            {"field": i, "sortable": True}
            for i in ["x", "y", "size", "mean_intensity", "blobId"]
        ],
        rowData=[],
    ),
    width=6,
)


blobTable_layout = html.Div([results_table])
