import pymongo
from settings import dbConn
from pprint import pprint
import numpy as np
from joblib import Memory
from time import time
from functools import wraps
from settings import USER
from dash import html
import dash_ag_grid as dag
import pandas as pd

memory = Memory(".npCacheDir", verbose=0)


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        #        print("func:%r args:[%r, %r] took: %2.4f sec" % (f.__name__, args, kw, te - ts))
        print("func:%r  took: %2.4f sec" % (f.__name__, te - ts))
        return result

    return wrap


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def getAnnotationElementCount(annotationName):
    match_query = {}  ## Currently not filtering on anything..
    # Define the aggregation pipeline
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": "$annotation.name",
                "total": {"$sum": 1},
                "with_elements": {
                    "$sum": {
                        "$cond": [{"$ifNull": ["$annotation.elements", False]}, 1, 0]
                    }
                },
            }
        },
        {
            "$project": {
                "annotationName": "$_id",
                "count": "$total",
                "count_with_elements": "$with_elements",
                "_id": 0,
            }
        },
        {"$sort": {"count": -1}},
    ]

    results = list(dbConn["annotationData"].aggregate(pipeline))
    return results


def insertAnnotationData(annotationItems, userName, debug=False):
    ### This will insert all of the annotations pulled from the DSA and
    #

    annotationItems = [dict(item, **{"userName": userName}) for item in annotationItems]
    ## TO DO: Change all the keys from _id to dsaID.. need to see if this breaks anything else

    operations = []
    for a in annotationItems:
        operations.append(
            pymongo.UpdateOne({"_id": a["_id"]}, {"$set": a}, upsert=True)
        )
    for chunk in chunks(operations, 500):
        result = dbConn["annotationData"].bulk_write(chunk)
        if debug:
            pprint(result.bulk_api_result)
    return result


def getAnnotationNameCount(userName, itemListFilter=None):
    """This will query the mongo database directly and get the distinct annotation names and the associated counts"""
    """The user name is added to segregate data
        The ItemListFilter will allow me to filter by a list of itemID's based on either the currentProject
        or currentTask depending on what options are passed otherwise it will return all annotations a user has access too
    
    """
    match_query = {"userName": USER}

    if itemListFilter:
        match_query["itemId"] = {"$in": itemListFilter}
    # # Select your collection
    collection = mc["annotationData"]

    # Define the aggregation pipeline
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": "$annotation.name",
                "total": {"$sum": 1},
                "with_elements": {
                    "$sum": {
                        "$cond": [{"$ifNull": ["$annotation.elements", False]}, 1, 0]
                    }
                },
            }
        },
        {
            "$project": {
                "annotationName": "$_id",
                "count": "$total",
                "count_with_elements": "$with_elements",
                "_id": 0,
            }
        },
        {"$sort": {"count": -1}},
    ]

    # s# # Execute the aggregation pipeline
    results = list(collection.aggregate(pipeline))
    return results


def generate_generic_DataTable(df, id_val, col_defs={}, exportable=False):
    # print("Dataframe type?")
    # print(type(df))

    # if type(df == list):
    #     df = pd.DataFrame(df)

    col_defs = [{"field": col} for col in df.columns] if not col_defs else col_defs

    dsa_datatable = html.Div(
        [
            dag.AgGrid(
                id=id_val,
                enableEnterpriseModules=True,
                className="ag-theme-alpine-dark",
                defaultColDef={
                    "filter": "agSetColumnFilter",
                    # "editable": True,
                    # "flex": 1,
                    "filterParams": {"debounceMs": 2500},
                    "floatingFilter": True,
                    "sortable": True,
                    "resizable": True,
                },
                columnDefs=col_defs,
                rowData=df.to_dict("records"),
                dashGridOptions={
                    "pagination": True,
                    "paginationAutoPageSize": True,
                    "rowSelection": "single",
                },
                # columnSize="sizeToFit",
                csvExportParams={
                    "fileName": f"{id_val.replace('-', '_')}.csv",
                }
                if exportable
                else {},
                style={"height": "75vh"},
            ),
        ]
    )

    return dsa_datatable
