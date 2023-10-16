from dash import html
from dash import Input, Output, State, ALL, callback
import dash_bootstrap_components as dbc
from settings import DSA_BASE_URL, gc
import dash
from pprint import pprint
from dash import html, Input, Output, State, dcc, callback_context, callback
import dash, json
import plotly.graph_objects as go

# from ...utils.api import get_item_rois, pull_thumbnail_array, get_largeImageInfo
import numpy as np
import plotly.express as px
import dash.dcc as dcc
import pickle
from settings import dbConn
import dbHelpers as dbh

### This will generate a dataview component, similar to what we have been using in Webix
## It expects a list of dictionaries, and then we can have various templates depending on
## what type of visualization we want, can also add the keys to display on the template, etc

# Define the image and page sizes for each option
sizes = {
    "small": {"image_size": "128px", "page_size": 12},
    "medium": {"image_size": "192px", "page_size": 10},
    "large": {"image_size": "256px", "page_size": 5},
}


images_per_row = {
    "small": 6,
    "medium": 5,
    "large": 3,
}


def getThumbnailUrl(imageId, encoding="PNG", height=128):
    ### Given an imageId, turns this into a URL to fetch the image from a girder server
    ## including the token
    thumb_url = f"{DSA_BASE_URL}/item/{imageId}/tiles/thumbnail?encoding={encoding}&height={height}&token={gc.token}"
    return thumb_url


cardTemplates = {}


def generate_cards(subset, selected_size, cardType="image"):
    cards_and_tooltips = []

    print("Card Type was set to", cardType)
    for index, item in enumerate(subset):
        card_id = f"card-{index}"
        column_width = 12 // images_per_row[selected_size]

        if cardType == "annotationDoc":
            cards_and_tooltips.append(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    plotImageAnnotations(item["itemId"]),
                                    html.H6(
                                        item.get("annotation", None).get("name", None),
                                        className="card-title no-wrap",
                                    ),
                                ],
                                style={
                                    "height": sizes[selected_size]["image_size"],
                                    "width": sizes[selected_size]["image_size"],
                                },
                            ),
                        ],
                        className="mb-6",
                        # style={"width": "192px", "height": "192px", "margin": "2px"},
                        id=card_id,  # add id to each card
                    ),
                    md=column_width,  # Adjusted column width
                )
            )
        else:
            cards_and_tooltips.append(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardImg(
                                src=getThumbnailUrl(item["_id"]),
                                top=True,
                                style={
                                    "height": sizes[selected_size]["image_size"],
                                    "width": sizes[selected_size]["image_size"],
                                },
                            ),
                            dbc.CardBody(
                                [
                                    html.H6(
                                        item.get("name", "None"),
                                        className="card-title no-wrap",
                                    ),
                                ]
                            ),
                        ],
                        className="mb-4",
                        style={"width": "192px", "height": "192px", "margin": "2px"},
                        id=card_id,  # add id to each card
                    ),
                    md=column_width,  # Adjusted column width
                )
            )

        cards_and_tooltips.append(
            dbc.Tooltip(
                f"Row: {index//3 + 1}, Column: {(index%3) + 1}",
                target=card_id,
            )
        )

    return cards_and_tooltips


def generateDataViewLayout(itemSet, type="imageList"):
    size_selector = dbc.RadioItems(
        id="size-selector",
        options=[{"label": size.capitalize(), "value": size} for size in sizes],
        value="large",  # Default value
        inline=True,
    )

    initial_max_page = (len(itemSet) // sizes["small"]["page_size"]) + (
        1 if len(itemSet) % sizes["small"]["page_size"] > 0 else 0
    )
    pagination = dbc.Pagination(
        id="pagination",
        size="sm",
        active_page=1,
        fully_expanded=False,
        first_last=True,
        previous_next=True,
        max_value=initial_max_page,
    )

    # We will initially display only the first page of cards. The callback will handle subsequent updates.
    active_page = 1
    start_idx = (active_page - 1) * sizes["small"]["page_size"]
    end_idx = start_idx + sizes["small"]["page_size"]
    # cards_and_tooltips = generate_cards(itemSet[start_idx:end_idx], "small")

    # cards = dbc.Row(cards_and_tooltips, justify="start")
    return [
        html.Div([size_selector, pagination]),  # Put these controls in a Div at the top
        html.Div(id="cards-container"),  # This Div will be populated by the callback
    ]


@callback(
    [Output("pagination", "max_value"), Output("cards-container", "children")],
    [Input("pagination", "active_page"), Input("size-selector", "value")],
    [State("filteredItem_store", "data")],
)
def update_cards_and_pagination(active_page, selected_size, itemSet):
    if not itemSet or not active_page or not selected_size:
        return dash.no_update, dash.no_update

    cards_per_page = sizes.get(selected_size, {}).get("page_size", 0)
    if not cards_per_page:
        return dash.no_update, dash.no_update

    start_idx = (active_page - 1) * cards_per_page
    end_idx = start_idx + cards_per_page

    cards_and_tooltips = generate_cards(
        itemSet.get("data", [])[start_idx:end_idx],
        selected_size,
        itemSet.get("displayType", None),
    )
    cards = dbc.Row(cards_and_tooltips, justify="start")

    max_page = (len(itemSet["data"]) // cards_per_page) + (
        1 if len(itemSet["data"]) % cards_per_page > 0 else 0
    )

    return max_page, cards


def getAnnotationShapesForItem(itemId, annotationName):
    ## This will determine if mongo already has the elements data for the annotation, if not it will pull it, and cache it
    ## just looking up tissue for now..
    annotationName = "tissue"

    ## Find all the annotations available for the currently selecetd itemId and annotationName
    availableAnnotations = dbConn["annotationData"].find(
        {"itemId": itemId, "annotation.name": annotationName}
    )

    for aa in availableAnnotations:
        if "elements" not in aa.get("annotatoins", {}):
            ## Need to get the elements from girder... this takes a long time at scale

            annotElements = gc.get(f"annotation/{aa['_id']}")
            if annotElements:
                ## Update Mongo..
                dbh.insertAnnotationData([annotElements])

    ## Now that I have checked everything is in mongo.. requery and pull the entire thing
    availableAnnotations = dbConn["annotationData"].find(
        {"itemId": itemId, "annotation.name": annotationName}
    )
    return list(availableAnnotations)


def plotImageAnnotations(
    imageId, annotationName="ManualGrayMatter", plotSeparateShapes=False
):
    """Given an image ID, will plot available annotations.. in the future this will
    maybe be fancier and we can select which annotation to draw if there are several.. but this requires
    a separate panel and gets more complicated

    By default, I am not going to show every shape individually, although in the future I may want to do
    stats and double check individual shape obhects are actually closed
    What I am talking about is that say we are drawing ROIs or drawing a gray matter boundary.  Even though
    every shape is an ROI, or every shape is gray matter, I could potentially draw them as different polygons
    so I may (or may not) want to merge the shapes into a single labeled object, or keep them separate.
    This will be expanded upon going forward..
    """

    ## TO DO: Cache this?
    pickledItem = gc.get(
        f"item/{imageId}/tiles/thumbnail?encoding=pickle", jsonResp=False
    )

    ## Need to have or cache the baseImage size as well... another feature to add

    baseImage_as_np = pickle.loads(pickledItem.content)
    annotFig = go.Figure(
        px.imshow(baseImage_as_np)
    )  # , color_continuous_scale="gray"))

    imageSizeInfo = gc.get(f"item/{imageId}/tiles")  ### I should probably cache this...

    # if there are no ROIs, no need to do anything but return the image for viz

    ## Adding in code to cache elements if they are not available...

    # imageAnnotationRawData = gc.get(f"annotation?itemId={imageId}&text=tissue")
    # imageAnnotationData = []

    imageAnnotationData = getAnnotationShapesForItem(imageId, annotationName)

    # for ia in imageAnnotationRawData:
    #     imageAnnotationData.append(gc.get(f"annotation/{ia['_id']}"))

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
            # print(cpa)
            # if cpa:

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

    ## May want to eventually add a check that pulls the point data if an item does not have any elements
    ## This is a future enhancement
