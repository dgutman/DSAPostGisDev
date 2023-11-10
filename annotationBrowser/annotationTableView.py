### This displays the list of avialable annotations in tabular format instead of as a dataview
from dash import html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash
from settings import dbConn, gc, USER
from app_config import SingletonDashApp  # , background_callback_manager
import dbHelpers as dbh
from pprint import pprint
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

## Trying to add diskcache functionality
import diskcache

# from dash.long_callback import DiskcacheLongCallbackManager

cache = diskcache.Cache("./cache", timeout=10)
background_callback_manager = dash.DiskcacheManager(cache)

## Creating tables here..
curAppObject = SingletonDashApp()

app = curAppObject.app

button_controls = html.Div(
    [
        html.Button(
            id="cancel_button_id",
            className="mr-2 btn btn-danger",
            children="Cancel Running Job!",
        ),
        html.Button(
            "Refresh anotation data",
            className="mr-2 btn btn-primary",
            id="refresh-annotations-button",
        ),
        html.Button(
            "Pull Full Annotation",
            id="pull-full-annotation-button",
            className="mr-2 btn btn-warning",
        ),
        html.Button(
            "Clear Cache",
            id="clear-cache-button",
            className="mr-2 btn btn-warning",
        ),
    ],
    className="d-grid gap-2 d-md-flex justify-content-md-begin",
)

unique_annots_datatable = html.Div([], id="unique_annots_datatable_div")

## This provides details depending on the type of annotation being displayed..
annotation_details_panel = html.Div(id="annotation_details_panel")

unique_params_datatable = html.Div(
    [html.Div(id="annotation_name_counts_table")], id="unique_params_datatable_div"
)


annotationTable_layout = dbc.Container(
    dbc.Row(
        [
            button_controls,
            dbc.Progress(
                id="annotationDetails_update_pbar",
                className="progress-bar-success",
                style={"visibility": "hidden", "width": 250},
            ),
            html.Div(id="annotationPull_status"),
            html.Div(id="annotationCount_tableDiv"),
            html.Div(id="dbStatus_output"),
            dbc.Row(
                [
                    dbc.Col([unique_annots_datatable], width=5),
                    dbc.Col(
                        [dbc.Row([unique_params_datatable])],
                        width=2,
                    ),
                    dbc.Col(annotation_details_panel, width=5),
                ]
            ),
        ]
    )
)


@callback(
    Output("annotationCount_tableDiv", "children"),
    Input("refresh-annotations-button", "n_clicks"),
)
def generateAnnotationCountTable(n_clicks):
    ### This fires initially, and can be updated manually because the table may get upgraded in the background

    elementCount = dbh.getAnnotationElementCount("tissue")

    elementCountTable = dbh.generate_generic_DataTable(
        pd.DataFrame(elementCount), "annotElementCount_table"
    )

    return elementCountTable


# @callback(
#     Output("dbStatus_output", "children"), Input("clear-cache-button", "n_clicks")
# )
# def clearDataCache(n_clicks):
#     """This fires if the clear cache button is fired, this should delete both the mongo data and any cached npArray data"""
#     totalDocCount = dbConn["annotationData"].count_documents({})

#     ## Fire off asynchronous callback
#     elementCount = dbh.getAnnotationElementCount("tissue")

#     elementCountTable = dbh.generate_generic_DataTable(
#         pd.DataFrame(elementCount), "annotElementCount_table"
#     )

#     return elementCountTable

#     if n_clicks:
#         print("Clearing cache..")
#         dbConn["annotationData"].delete_many({})
#         ## Should include the username in the next version..


@callback(
    output=Output("annotationPull_status", "children"),
    inputs=[
        Input("pull-full-annotation-button", "n_clicks"),
    ],
    running=[
        (Output("pull-full-annotation-button", "disabled"), True, False),
        (Output("cancel_button_id", "disabled"), False, True),
        (
            Output("annotationPull_status", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("annotationDetails_update_pbar", "style"),
            {"visibility": "visible"},
            {"visibility": "hidden"},
        ),
        (
            Output("annotationDetails_update_pbar", "style"),
            {"visibility": "visible"},
            {"visibility": "visible"},
        ),
    ],
    cancel=Input("cancel_button_id", "n_clicks"),
    progress=[
        Output("annotationDetails_update_pbar", "value"),
        Output("annotationDetails_update_pbar", "label"),
    ],
    prevent_initial_call=True,
    # background=True,
    # manager=background_callback_manager,
)
# set_progress,
def pull_annotation_elements(n_clicks, max_workers=5):
    if n_clicks:
        collection = dbConn["annotationData"]
        USER = "admin"
        docCount = collection.count_documents(
            {"annotation.elements": {"$exists": False}, "userName": USER}
        )
        print(f"There are a total of {docCount} annotations to look up")

        if docCount == 0:
            return dash.no_update

        if docCount > 1000:
            docCount = 1000  ## For debugging want to put a limit on this

        docsWithNoElements = collection.find(
            {"annotation.elements": {"$exists": False}, "userName": USER}
        ).limit(docCount)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Distribute the work across the threads
            futures = [
                executor.submit(
                    update_annotation, set_progress, i, docsWithNoElements, USER
                )
                for i in range(docCount)
            ]

            # Wait for all futures to complete
            concurrent.futures.wait(futures)

        return dash.no_update


# def pull_annotation_elements(set_progress, n_clicks):
#     """When I pull annotation in bulk, we do not return individual elelements
#     as if can be very slow, so this will grab elements in the background and update"""
#     # print(n_clicks)
#     if n_clicks:
#         # print("Something indeed was clicked...")
#         collection = dbConn["annotationData"]

#         ## Fix logic here in case there aRE no documents with missing elements..
#         # Count documents where the "elements" key does not exist filtered by USER
#         ## This may eventually cause errors if multiple users have access to the same annotation
#         USER = "admin"

#         docCount = collection.count_documents(
#             {"annotation.elements": {"$exists": False}, "userName": USER}
#         )

#         print(f"There are a total of {docCount} annotations to look up")
#         docCount = 1000

#         for i in range(docCount):
#             ## pull and update a single annotation document
#             # find a document that has no elements
#             if i % 50 == 0:
#                 print(i)
#             doc_with_no_element = collection.find_one(
#                 {"userName": USER, "annotation.elements": {"$exists": False}}
#             )
#             ## Now pull the data from the api
#             # print(doc_with_no_element)
#             # print(gc.token, "is token..")
#             fullAnnotationDoc = gc.get(f"annotation/{doc_with_no_element['_id']}")
#             collection.update_one(
#                 {"_id": doc_with_no_element["_id"], "userName": USER},
#                 {"$set": fullAnnotationDoc},
#             )

#             jobStatuspercent = ((i + 1) / docCount) * 100
#             set_progress((str(i + 1), f"{jobStatuspercent:.2f}%"))
#         return dash.no_update
# return [f"Clicked {n_clicks} times"] ## I actually don't want this div to be updated

# if nometa_button:
#     with ThreadPoolExecutor() as executor:
#         results = list(
#             executor.map(
#                 process_row, itemlist_data, [s.COLS_FOR_COPY] * len(itemlist_data)
#             )
#         )

#     return results, "merged-data"


import concurrent.futures


def update_annotation(set_progress, i, docList, USER):
    collection = dbConn["annotationData"]
    # Find a document that has no elements
    doc_with_no_element = docList[i]
    # print(i, doc_with_no_element)
    # If no document is found, return early
    if doc_with_no_element is None:
        return

    # Pull the data from the API
    fullAnnotationDoc = gc.get(f"annotation/{doc_with_no_element['_id']}")

    itemInfo = gc.get(f'item/{doc_with_no_element["itemId"]}')
    imageName = itemInfo["name"]

    fullAnnotationDoc["imageName"] = imageName

    # Update the document in the database
    status = collection.update_one(
        {"_id": doc_with_no_element["_id"], "userName": USER},
        {"$set": fullAnnotationDoc},
    )
    # print(status)
    # Update the progress
    jobStatuspercent = ((i + 1) / len(docList)) * 100
    set_progress((str(i + 1), f"{jobStatuspercent:.2f}%"))
