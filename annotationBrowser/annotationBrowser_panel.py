from dash import html, callback, Input, Output, State, dcc
import dash_bootstrap_components as dbc
import os, json
from settings import gc, dbConn
from dataView_component import generateDataViewLayout
from pprint import pprint
import pymongo
import dbHelpers as dbh

annotationDocs = ["tissue", "gray"]


annotation_panel = html.Div(
    [
        dcc.Store("filteredItem_store", data=[]),
        dbc.Button("Pull Annotaton Data", id="pullAnnotationData-button"),
        dbc.Select(
            id="annotationDocName_select",
            options=annotationDocs,
            value=annotationDocs[0],
            style={"maxWidth": 200},
        ),
        html.Div(id="annotationStatsPanel"),
        html.Div(
            id="images_div",
            children=[
                dbc.Pagination(
                    id="pagination",
                    size="md",
                    active_page=1,
                    max_value=1,
                ),
                html.Div(
                    id="cards-container",
                    style={
                        "display": "flex",
                        "justify-content": "space-around",
                        "flex-wrap": "wrap",
                        "max-width": "400px",
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
    Output("annotationStatsPanel", "children"),
    Input("pullAnnotationData-button", "n_clicks"),
)
def pullAnnotationStats(n_clicks):
    print("A button was pressed I think")
    totalDocCount = dbConn["annotationData"].count_documents({})

    elementCount = dbh.getAnnotationElementCount("tissue")
    pprint(elementCount)

    return html.Div(f"Total Doc Count: {totalDocCount}")


@callback(
    Output("images_div", "children"),
    Input("filteredItem_store", "data"),
)
def generateAnnotationDataViewPanel(annotationData):
    ## TO BE REPLACED WITH DATABASE CALLS IN THE NEAR FUTURE

    ## This is where I am addending the type
    return generateDataViewLayout(annotationData)


def getAnnotationData_from_mongo(annotationName, debug=False):
    ### This will insert all of the annotations pulled from the DSA and
    result = dbConn["annotationData"].find(
        {"annotation.name": annotationName}, {"annotation.elements": 0}
    )
    ## Remeber this thing is a cursor, you may also want to prefilter out some of the fields that we don't need
    if result:
        return list(result)
    else:
        return [{}]


## Simple function to pull annotations based on the name from the DSA itself..
def lookupImageAnnotationsByName(annotationName, limit=0, refreshDataBase=True):
    ## See if any documents exist for the
    collection = dbConn["annotationData"]

    docCount = collection.count_documents({})

    if not docCount or refreshDataBase:
        annotationDocs = gc.get(f"annotation?text={annotationName}&limit={limit}")

        if annotationDocs:
            dbh.insertAnnotationData(annotationDocs)

    annotationDocs = getAnnotationData_from_mongo(annotationName)
    return annotationDocs


@callback(
    Output("filteredItem_store", "data"),
    Input("annotationDocName_select", "value"),
)
def updateItemStore(annotationName):
    if annotationName:
        annotationDocs = lookupImageAnnotationsByName(annotationName)
        return {"displayType": "annotationDoc", "data": annotationDocs}
