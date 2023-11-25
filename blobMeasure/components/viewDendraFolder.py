import girder_client, json
import dotenv, os, girder_client
import dash_ag_grid as dag
from joblib import Memory
from dbHelpers import generate_generic_DataTable
from dash import html, Input, State, Output, callback
import pandas as pd
import re
from dbHelpers import getImageThumb_as_NP, plotImageAnnotations
import dash_bootstrap_components as dbc

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


df = parseExperimentFolder(denraFolderId)

##Generate area to show image of selected row
imageView_row = html.Div(id="selectedImage_viz")


sampleExpGrid = generate_generic_DataTable(df, "experimentTable")

experimentView_panel = html.Div(
    [
        html.Button(id="dosomething"),
        dbc.Row([sampleExpGrid], style={"height": "50vh"}),
        dbc.Row([html.Div(id="selectedImage_viz")]),
    ]
)


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


#        image_as_np = getImageThumb_as_NP(selected[0]["_id"])

# image_fig = plotImageAnnotations(imageId)
# image_copy = getImageThumb_as_NP(imageId)
# image_copy = getImageThumb_as_NP(imageId)
# image_with_contours = image_copy.copy()
# orig_shape = (image_copy.shape[1], image_copy.shape[0])
# image_copy = image_copy[:, :, :3]
# image = val_transforms(image_copy)
# with torch.set_grad_enabled(False):
#     image = image.unsqueeze(0)
#     pred = model(image)
# pred = (pred[0][0] > 0.5).data.cpu().numpy()

#      fig = go.Figure(data=[image_with_contours_trace], layout=layout)
