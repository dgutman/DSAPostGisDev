from dash import html, callback, Input, Output, State, dcc
import dash_bootstrap_components as dbc
import os, json
from settings import gc
from dataView_component import generateDataViewLayout

annotationDocs = ["tissue", "gray"]

annotation_panel = html.Div(
    [
        dcc.Store("filteredItem_store", data=[]),
        dbc.Select(
            id="annotationDocName_select",
            options=annotationDocs,
            value=annotationDocs[0],
            style={"maxWidth": 200},
        ),
        html.Div(
            id="images_div",
            children=[
                dbc.Pagination(
                    id="pagination",
                    size="sm",
                    active_page=1,
                    max_value=1,
                ),
                html.Div(
                    id="cards-container",
                    style={
                        "display": "flex",
                        "justify-content": "space-around",
                        "flex-wrap": "wrap",
                        "max-width": "300px",
                    },
                ),
                dbc.RadioItems(
                    id="size-selector",
                    value="small",  # Default value
                    inline=True,
                ),
            ],
            style={"overflow-y": "auto", "max-height": "100vh"},
        ),
    ]
)


@callback(
    Output("images_div", "children"),
    Input("filteredItem_store", "data"),
)
def generateAnnotationDataViewPanel(annotationData):
    ## TO BE REPLACED WITH DATABASE CALLS IN THE NEAR FUTURE

    ## This is where I am addending the type
    return generateDataViewLayout(annotationData)


@callback(
    Output("filteredItem_store", "data"),
    Input("annotationDocName_select", "value"),
)
def updateItemStore(annotationName):
    if annotationName:
        print("Should only be looking up", annotationName)
        annotationDocs = gc.get(f"annotation?text={annotationName}&limit=2")
        return {"displayType": "annotationDoc", "data": annotationDocs}
