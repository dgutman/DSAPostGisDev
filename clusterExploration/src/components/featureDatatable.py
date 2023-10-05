### This will generate a basic dash datatable we can use to look at whatever data set we are loading..
## Can add pretty formatting later for bonus points

import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, State
from ..utils.helpers import load_dataset, generate_generic_DataTable
from dash import dcc
import plotly.express as px
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler

sampleCSVFile = "MAP01938_0000_0E_01_region_001_quantification.csv"


# sampleCSVFile = "MedStats_MAP01938_0000_0E_01_region_001.csv"

## This is a bad idea.. this should be done as part of a callback function.. but I'll show you that later

df = load_dataset(sampleCSVFile)
data = pd.DataFrame(df)
all_columns = data.columns
filtered_columns = [col for col in all_columns if col.startswith("intensity")]
data = data.iloc[0:2000]
data = data[filtered_columns]
scaler = StandardScaler()
data[filtered_columns] = scaler.fit_transform(data[filtered_columns])
cluster = AgglomerativeClustering(n_clusters=3, affinity="euclidean", linkage="ward")

cluster.fit(data.values)
labels = cluster.labels_
data["Cluster labels"] = labels

my_first_datable = generate_generic_DataTable(
    data, "cluster-feature-datatable", col_defs={}, exportable=False
)


intensity_cols = [col for col in df.columns if "intensity" in col]


my_second_row = dbc.Row(
    [
        dbc.Col(id="left-col-stats", width=4),
        dbc.Col(
            dbc.Row(
                [
                    dcc.Slider(
                        0,
                        50000,
                        100,
                        value=10000,
                        id="area-slider",
                        marks=None,
                    ),
                    html.Div(id="middle-col-graph"),
                ]
            ),
            width=4,
        ),
        dbc.Col(
            dbc.Row(
                [
                    dbc.Select(
                        id="featureList_selector",
                        options=intensity_cols,
                        value=intensity_cols[0],
                        style={"maxWidth": 300},
                    ),
                    html.Div(id="right-col-graph"),
                ]
            ),
            width=4,
        ),
    ]
)

# my_third_row = dbc.Row([dbc.Col(id="left-col", width = 3),dbc.Col(id = "mid-col", width = 6), dbc.Col("Column Right", width=3)])

featureDataTable_layout = html.Div(
    [
        dcc.Store(id="rawFeatureData_store", data=df.to_dict("records")),
        dbc.Row([my_first_datable]),
        my_second_row,
    ]
)


@callback(Output("left-col-stats", "children"), Input("rawFeatureData_store", "data"))
def arjitasFirstCoolCallback(clusterData):
    numCellsInDataSet = len(clusterData)
    return html.H3(f"There are {numCellsInDataSet} objects in the current dataset")


@callback(
    Output("middle-col-graph", "children"),
    Input("rawFeatureData_store", "data"),
    Input("area-slider", "value"),
)
def arjitasFirstGraph(clusterData, maxAreaValue):
    ## TO DO... add in some logic that sets the maximum X and or doesn't plot
    ## extreme outliars..
    df = pd.DataFrame(clusterData)

    df = df[df.area < maxAreaValue]

    fig = px.histogram(df, x="area")
    return dcc.Graph(figure=fig)


@callback(
    Output("right-col-graph", "children"),
    Input("rawFeatureData_store", "data"),
    Input("featureList_selector", "value"),
)
def IntensityHistogram(clusterData, featureName):
    df = pd.DataFrame(clusterData)
    # all_columns = df.columns
    # filtered_columns = [col for col in all_columns if col.startswith("intensity")]

    fig = px.histogram(
        clusterData,
        x=featureName,
        nbins=50,
        title=f"Histogram of Intensity {featureName.replace('intensity','')}",
    )
    fig.update_xaxes(title_text="Intensities")
    fig.update_yaxes(title_text="Frequency")
    return dcc.Graph(figure=fig)
