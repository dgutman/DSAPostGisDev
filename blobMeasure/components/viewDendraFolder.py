import girder_client, json
import dotenv, os, girder_client
import dash_ag_grid as dag
from joblib import Memory
from dbHelpers import generate_generic_DataTable, register_images_ver3
from dash import html, Input, State, Output, callback, dcc
import pandas as pd
import re
from dbHelpers import getImageThumb_as_NP, plotImageAnnotations
import dash_bootstrap_components as dbc
import concurrent.futures
import numpy as np
import pandas as pd

## Needto import this from one place
memory = Memory(".npCacheDir", verbose=0)

# Load API Key from the environment...
dotenv.load_dotenv(".env")
apiKey = os.getenv("DSAKEY")
gc = girder_client.GirderClient(apiUrl="https://megabrain.neurology.emory.edu/api/v1")
_ = gc.authenticate(apiKey=apiKey)


denraFolderId = "65551c06d4d8e688cd09c0fb"


imageNamePattern = re.compile(
    "(?P<expId>.*), (?P<markerId>.*), (?P<timePoint>\d+)DIV_(?P<color>.*).tif"
)


def parseExperimentFolder(folderId):
    experimentItems = list(gc.listItem(denraFolderId, limit=100))

    imageList = []
    for i in experimentItems:
        match = imageNamePattern.match(i["name"])

        if i["name"].endswith("tif"):
            dataRow = {"_id": i["_id"], "name": i["name"]}

            if match:
                # print(match.groupdict())
                dataRow.update(match.groupdict())
                dataRow["matched"] = True
            else:
                print("No match", i["name"])

            imageList.append(dataRow)
    df = pd.DataFrame(imageList)
    return df


import numpy as np

df = parseExperimentFolder(denraFolderId)

##Generate area to show image of selected row
imageView_row = html.Div(id="selectedImage_viz")


## Generate experiment list based on markerID from the current folder
experimentList = list(set(df.markerId.dropna()))


expCombo = dbc.Select(
    id="expSelect",
    options=experimentList,
    value=experimentList[0],
    style={"width": 300},
)


sampleExpGrid = dag.AgGrid(
    id="experimentTable",
    columnDefs=[{"field": x} for x in df.columns],
    rowData=df.to_dict("records"),
    defaultColDef={
        "filter": "agSetColumnFilter",
        "filterParams": {"debounceMs": 2500},
        "floatingFilter": True,
        "sortable": True,
        "resizable": True,
    },
    dashGridOptions={
        "pagination": True,
        "paginationAutoPageSize": True,
        "rowSelection": "single",
    },
    className="ag-theme-alpine-dark",
)


imageRegData_table = dag.AgGrid(
    id="imageRegTable",
    columnDefs=[
        {"field": "imageName"},
        {"field": "fixedImage"},
        {"field": "movingImage"},
        {"field": "fixedImage_id"},
        {"field": "movingImage_id"},
        {"field": "fixedImage_hash"},
        {"field": "movingImage_hash"},
        {"field": "forward_xfm"},
    ],
    defaultColDef={
        "filter": "agSetColumnFilter",
        "filterParams": {"debounceMs": 2500},
        "floatingFilter": True,
        "sortable": True,
        "resizable": True,
    },
    dashGridOptions={
        "pagination": True,
        "paginationAutoPageSize": True,
        "rowSelection": "single",
    },
    className="ag-theme-alpine-dark",
)


experimentView_panel = html.Div(
    [
        dbc.Row(
            [
                dcc.Store("experimentFolderData_store", data=df.to_dict("records")),
                html.Button(
                    "RegisterImageStack",
                    id="regImageStack_button",
                    style={"width": 200},
                ),
                expCombo,
            ]
        ),
        dbc.Row(sampleExpGrid, style={"flex": "2"}),  # Flex value of 1
        dbc.Row(
            [html.Div(id="selectedImage_viz")], style={"flex": "1"}
        ),  # Flex value of 1
        dbc.Row(imageRegData_table),
    ],
    style={"display": "flex", "flexDirection": "column", "height": "90vh"},
)


# def pullOrGenerateExperimentRegistrations(n_clicks, selectedExpData):
#     if n_clicks:
#         ##getImageThumb_as_NP(imageId, imageWidth=512):
#         ### Need to cycle throw the array for GREEN and RED separately
#         ## And also assume first Image in the series is the initial timePoint.. obviously
#         ## better just to sort
#         exp_df = pd.DataFrame(selectedExpData)
#         expStatusData = []
#         for r in selectedExpData:
#             print(r["name"])
#             regData = getImageRegPair(exp_df, r["_id"])

#             tableData = {"imageName": r["name"]}
#             tableData.update(regData)

#             expStatusData.append(tableData)
#         return expStatusData
#     return None


@callback(
    Output("imageRegTable", "rowData"),
    Input("regImageStack_button", "n_clicks"),
    State("experimentTable", "rowData"),
)
def pullOrGenerateExperimentRegistrations(n_clicks, selectedExpData):
    if n_clicks:
        exp_df = pd.DataFrame(selectedExpData)

        def process_registration(r):
            print(r["name"])
            regData = getImageRegPair(exp_df, r["_id"])
            tableData = {"imageName": r["name"]}
            tableData.update(regData)
            return tableData

        # Use ThreadPoolExecutor to run tasks in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            expStatusData = list(executor.map(process_registration, selectedExpData))

        return expStatusData


def getImageRegPair(experimentData, imageId):
    ### Given an imageID, this will try and find the appropriate image to register to it to
    ### The image should have the same color and also be the
    df = pd.DataFrame(experimentData)
    ## Capitalize the color column
    df.color = df.color.str.upper()
    # t timePoint to numeric (integer)
    df["timePoint"] = pd.to_numeric(df["timePoint"], errors="coerce").astype("Int64")

    row = df.loc[df["_id"] == imageId]
    if row.empty:
        return None
    else:
        inputImageData = row.iloc[0]
        ## Now find matching Row..
        ## This would be the first image
        movingImageName = inputImageData.to_dict()["name"]
        movingImage_id = inputImageData.to_dict()["_id"]

        df_sorted_filtered_asc = df[
            df.color == inputImageData.to_dict()["color"]
        ].sort_values(by="timePoint", ascending=True)
        fixedImageName = df_sorted_filtered_asc.iloc[0].to_dict()["name"]
        fixedImage_id = df_sorted_filtered_asc.iloc[0].to_dict()["_id"]

        fixedImage_npArray = getImageThumb_as_NP(fixedImage_id)
        movingImage_npArray = getImageThumb_as_NP(movingImage_id)

        # hash_value = np.array_hash(array)
        fixedImage_hash = hash(fixedImage_npArray.tobytes())
        movingImage_hash = hash(movingImage_npArray.tobytes())
        # try:
        image_xfms = register_images_ver3(fixedImage_npArray, movingImage_npArray)
        print(image_xfms)
        # except:
        #     print("Image Registration Failed")
        #     image_xfms = {}
        # print(image_xfms)

        # print(f"Generating registration from {movingImageName} to {fixedImageName}")
        return {
            "movingImage": movingImageName,
            "fixedImage": fixedImageName,
            "fixedImage_id": fixedImage_id,
            "movingImage_id": movingImage_id,
            "movingImage_hash": movingImage_hash,
            "fixedImage_hash": fixedImage_hash,
            "forward_xfm": image_xfms.get("xfm", None),
            "inv_xfm": image_xfms.get("inv_xfm", None),
        }

        ## Now get the dataframe sorted and filtered by color and then timePoint


# # Example usage
# image_id_to_lookup = 2
# result_dict = get_row_as_dict(df, image_id_to_lookup)


@callback(
    Output("experimentTable", "rowData"),
    Input("expSelect", "value"),
    Input("experimentFolderData_store", "data"),
)
def filterExperimentFolderForTable(expName, folderData):
    df = pd.DataFrame(folderData)

    df = df[df.markerId == expName]
    return df.to_dict("records")


@callback(
    Output("selectedImage_viz", "children"),
    Input("experimentTable", "selectedRows"),
)
def showSelectedImage(selectedRow):
    if selectedRow:
        imageId = selectedRow[0]["_id"]
        # imageThumb = getImageThumb_as_NP(imageId)
        imageThumb = plotImageAnnotations(imageId)
        return imageThumb
