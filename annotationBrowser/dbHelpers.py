import pymongo
from settings import dbConn
from pprint import pprint
import numpy as np
from joblib import Memory
from time import time
from functools import wraps
from settings import USER, gc
from dash import html, dcc
import dash_ag_grid as dag
import pandas as pd
import pickle
import plotly.graph_objects as go

# from ...utils.api import get_item_rois, pull_thumbnail_array, get_largeImageInfo
import numpy as np
import plotly.express as px

from settings import DSA_BASE_URL, gc

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


def getAnnotationShapesForItem(itemId, annotationName):
    ## This will determine if mongo already has the elements data for the annotation, if not it will pull it, and cache it
    ## just looking up tissue for now..

    ## Find all the annotations available for the currently selecetd itemId and annotationName
    availableAnnotations = dbConn["annotationData"].find(
        {"itemId": itemId, "annotation.name": annotationName}
    )
    for aa in availableAnnotations:
        if "elements" not in aa.get("annotation", {}):
            ## Need to get the elements from girder... this takes a long time at scale
            annotElements = gc.get(f"annotation/{aa['_id']}")
            itemName = getItemName(aa["itemId"], "admin")
            annotElements["itemName"] = itemName

            if annotElements:
                ## Update Mongo..
                insertAnnotationData([annotElements], USER)

    ## Now that I have checked everything is in mongo.. requery and pull the entire thing
    availableAnnotations = dbConn["annotationData"].find(
        {"itemId": itemId, "annotation.name": annotationName}
    )
    return list(availableAnnotations)


@timing
def plotImageAnnotations(
    imageId, annotationName="ManualGrayMatter", plotSeparateShapes=False
):
    """Given an image ID, will plot available annotations.. in the future this will
    maybe be fancier and we can select which annotation to draw if there are several.. but this requires
    a separate panel and gets more complicated

    By default, I am not going to show every shape individually, although in the future I may want to do
    stats and double check individual shape obhects are actually closed
    What I am talking about is that say we are drawing ROIs or drawing gray matter boundary.  Even though
    every shape is an ROI, or every shape is gray matter, I could potentially draw them as different polygons
    so I may (or may not) want to merge the shapes into a single labeled object, or keep them separate.
    This will be expanded upon going forward..
    """

    ## Need to have or cache the baseImage size as well... another feature to add
    try:
        baseImage_as_np = getImageThumb_as_NP(imageId)

        annotFig = go.Figure(px.imshow(baseImage_as_np))
    except:
        print("Something wrong when getting image", imageId)
        return None
    ## This pulls the mm_x, mm_y and full resolution for the given image
    imageSizeInfo = getImageInfo(imageId)

    # if there are no ROIs, no need to do anything but return the image for viz
    imageAnnotationData = getAnnotationShapesForItem(imageId, annotationName)

    x_scale_factor = imageSizeInfo["sizeX"] / baseImage_as_np.shape[1]
    y_scale_factor = imageSizeInfo["sizeY"] / baseImage_as_np.shape[0]

    for a in imageAnnotationData:
        elementList = a["annotation"]["elements"]
        annotationName = a["annotation"]["name"]
        combinedPtArray = []

        for e in elementList:
            if "points" in e:
                ptArray = np.array(e["points"])[:, :2]

                combinedPtArray.extend(ptArray.tolist())
                combinedPtArray.append([None, None])
                if plotSeparateShapes:
                    annotFig.add_trace(
                        go.Scatter(
                            x=ptArray[:, 0] / x_scale_factor,
                            y=ptArray[:, 1] / y_scale_factor,
                            name=annotationName,
                        )
                    )
        # After exiting the loop, remove the last [None, None] (if any) before stacking to create the numpy array
        if combinedPtArray and combinedPtArray[-1] == [None, None]:
            combinedPtArray.pop()

        if combinedPtArray:
            # cpa = np.vstack(combinedPtArray)
            cpa = combinedPtArray
        else:
            cpa = np.array([])
        # print(cmp)

        if len(cpa):
            x_values = [
                (pt[0] / x_scale_factor if pt[0] is not None else None) for pt in cpa
            ]
            y_values = [
                (pt[1] / y_scale_factor if pt[1] is not None else None) for pt in cpa
            ]

            ## Maybe add a flag here based on whether I output the merged or the one above..
            annotFig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    name=annotationName + "-merged",
                    mode="lines+markers",
                )
            )

    annotFig.update_layout(
        margin=dict(l=0, r=0, b=0, t=0),  # removes margins
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False),
        plot_bgcolor="white",  # background of the plotting area
        paper_bgcolor="white",
        legend=dict(
            x=0.5,
            y=0.1,
            traceorder="normal",
            orientation="h",
            valign="top",
            xanchor="center",
            yanchor="top",
        ),
    )

    return dcc.Graph(
        figure=annotFig,
        style={"width": "100%", "height": "100%"},
        config={"displayModeBar": False},  # this removes the toolbar
    )


def getImageInfo(imageId):
    ## This will return the size and other params for the image
    ## Pull data from mongo...
    imageTileInfo = dbConn["imageTileInfo"].find_one({"imageId": imageId})
    if imageTileInfo:
        return imageTileInfo
    else:
        imageSizeInfo = gc.get(
            f"item/{imageId}/tiles"
        )  ### I should probably cache this...
        imageSizeInfo["imageId"] = imageId
        dbConn["imageTileInfo"].insert_one(imageSizeInfo)

    imageTileInfo = dbConn["imageTileInfo"].find_one({"imageId": imageId})

    return imageTileInfo


@memory.cache
def getImageThumb_as_NP(imageId, imageWidth=512):
    ## TO DO: Cache this?
    try:
        pickledItem = gc.get(
            f"item/{imageId}/tiles/thumbnail?encoding=pickle&frame=0", jsonResp=False
        )
        ## Need to have or cache the baseImage size as well... another feature to add
        baseImage_as_np = pickle.loads(pickledItem.content)
    except:
        return None

    # print("Retreived an image..")
    return baseImage_as_np


def getThumbnailUrl(imageId, encoding="PNG", height=128):
    ### Given an imageId, turns this into a URL to fetch the image from a girder server
    ## including the token
    thumb_url = f"{DSA_BASE_URL}/item/{imageId}/tiles/thumbnail?encoding={encoding}&height={height}&token={gc.token}"
    return thumb_url


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


def insertItemData(itemList, userName, debug=False):
    ## This will insert item data into mongo for when I am in annotaition Mode specifically.
    itemList = [dict(item, **{"userName": userName}) for item in itemList]
    operations = []
    for i in itemList:
        operations.append(
            pymongo.UpdateOne({"_id": i["_id"]}, {"$set": i}, upsert=True)
        )

    ### NEED TO REDO THIS AND REMAP THE _id to annotationId or itemId... and keep the username field

    for chunk in chunks(operations, 500):
        result = dbConn["itemData"].bulk_write(chunk)
        if debug:
            pprint(result.bulk_api_result)
    return


def getItemName(itemId, userName):
    ### I want to either store or get itemData from Mongo or the DSA

    conn = dbConn["itemData"]
    itemData = conn.find_one({"_id": itemId, "userName": userName})
    if not itemData:
        itemData = gc.get(f"item/{itemId}")
        if itemData:
            insertItemData([itemData], userName)

            return itemData["name"]

    return itemData["name"]


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
