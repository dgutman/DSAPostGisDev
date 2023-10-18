from dash import html, callback, Input, Output, State, dcc
import dash_bootstrap_components as dbc
import os, json
from settings import gc, dbConn, USER
from dataView_component import generateDataViewLayout
from pprint import pprint
import pymongo
import dbHelpers as dbh
from functools import wraps
from time import time
from dbHelpers import timing

annotationDocs = ["tissue", "gray", "ManualGrayMatter"]

annotation_panel = html.Div(
    [
        dcc.Store("filteredItem_store", data=[]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "Pull Annotaton Data",
                            id="pullAnnotationData-button",
                            className="me-2",
                        )
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Select(
                            id="annotationDocName_select",
                            options=annotationDocs,
                            value=annotationDocs[0],
                            style={"maxWidth": 200},
                            className="mr-2",
                        )
                    ],
                    width=2,
                ),
                dbc.Col([html.Div(id="annotationStatsPanel")], width=2),
            ]
        ),
        dbc.Row(
            id="images_div",
            children=[
                dbc.Pagination(id="pagination", max_value=0),
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
@timing
def pullAnnotationStats(n_clicks):
    totalDocCount = dbConn["annotationData"].count_documents({})

    ## Fire off asynchronous callback
    # elementCount = dbh.getAnnotationElementCount("tissue")
    # pprint(elementCount)

    return html.Div(f"Total Doc Count: {totalDocCount}")


@callback(
    Output("images_div", "children"),
    Input("filteredItem_store", "data"),
)
def generateAnnotationDataViewPanel(annotationData):
    ## TO BE REPLACED WITH DATABASE CALLS IN THE NEAR FUTURE
    ## This is where I am addending the type
    return generateDataViewLayout(annotationData)


@timing
def getAnnotationData_from_mongo(annotationName, USER, debug=False):
    ### This will insert all of the annotations pulled from the DSA and
    result = dbConn["annotationData"].find(
        {"userName": USER, "annotation.name": annotationName},
        {"annotation.elements": 0},
    )
    ## Remeber this thing is a cursor, you may also want to prefilter out some of the fields that we don't need
    if result:
        return list(result)
    else:
        return [{}]


## Simple function to pull annotations based on the name from the DSA itself..
@timing
def lookupImageAnnotationsByName(annotationName, limit=0, refreshDataBase=False):
    ## See if any documents exist for the
    collection = dbConn["annotationData"]
    docCount = collection.count_documents({"annotation.name": "annotationName"})
    print(f"Found {docCount} docs with {annotationName}")
    if not docCount or refreshDataBase:
        annotationDocs = gc.get(f"annotation?text={annotationName}&limit={limit}")

        if annotationDocs:
            dbh.insertAnnotationData(annotationDocs, USER)

    annotationDocs = getAnnotationData_from_mongo(annotationName, USER)
    return annotationDocs


@callback(
    Output("filteredItem_store", "data"),
    Input("annotationDocName_select", "value"),
)
@timing
def updateItemStore(annotationName):
    if annotationName:
        annotationDocs = lookupImageAnnotationsByName(annotationName)
        return {"displayType": "annotationDoc", "data": annotationDocs}
