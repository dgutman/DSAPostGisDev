from dash import html, Input, Output, State, callback
from settings import gc
from dbHelpers import generate_generic_DataTable
import pandas as pd
import dash_bootstrap_components as dbc
from dataView_component import getImageThumb_as_NP, plotImageAnnotations

sampleFolderId = "645b9e006df8ba8751a909dd"


itemList = list(gc.listItem(sampleFolderId))


df = pd.DataFrame(itemList)
col_defs = [{"field": "_id"}, {"field": "name"}]


tissueSegModel_panel = html.Div(
    [
        html.Div("Still need glasses?"),
        generate_generic_DataTable(df, "sampleImageList_table", col_defs),
        html.Div(id="modelOutput_div"),
    ]
)


@callback(
    Output("modelOutput_div", "children"),
    Input("sampleImageList_table", "selectedRows"),
)
def selected(selected):
    if selected:
        imageId = selected[0]["_id"]

        #        image_as_np = getImageThumb_as_NP(selected[0]["_id"])

        image_fig = plotImageAnnotations(imageId)

        return html.Div([html.Div(selected[0]["name"]), image_fig])

    return "No selections"
