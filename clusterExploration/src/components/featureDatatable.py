### This will generate a basic dash datatable we can use to look at whatever data set we are loading..
## Can add pretty formatting later for bonus points

import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, State
from ..utils.helpers import load_dataset,generate_generic_DataTable
from dash import dcc
import plotly.express as px
import pandas as pd



sampleCSVFile = "MAP01938_0000_0E_01_region_001_quantification.csv"


## This is a bad idea.. this should be done as part of a callback function.. but I'll show you that later

df = load_dataset(sampleCSVFile)


my_first_datable = generate_generic_DataTable(df, 'cluster-feature-datatable', col_defs={}, exportable=False)


my_second_row = dbc.Row([dbc.Col(id="left-col-stats",width=3),dbc.Col(id="middle-col-graph",width=6),dbc.Col("Column Right",width=3)])


featureDataTable_layout = html.Div(
    [
    dcc.Store(id="rawFeatureData_store",data=df.to_dict('records')),
    dbc.Row( [my_first_datable]),

     dcc.Slider(0, 50000, 100,
               value=10000,
               id='area-slider',
               marks=None, 
    ),
    my_second_row
    ]
)

@callback( Output("left-col-stats","children"),
          Input("rawFeatureData_store","data")
            )
def arjitasFirstCoolCallback( clusterData ):
    
    numCellsInDataSet = len(clusterData)
    
    return html.H3(f"There are {numCellsInDataSet} objects in the current dataset")




@callback( Output("middle-col-graph","children"),
          Input("rawFeatureData_store","data"),
           Input("area-slider","value") )
def arjitasFirstGraph( clusterData,maxAreaValue ):
    
    ## TO DO... add in some logic that sets the maximum X and or doesn't plot
    ## extreme outliars..
    df = pd.DataFrame(clusterData)

    df = df[df.area<maxAreaValue]

    fig = px.histogram(df, x="area")
    return dcc.Graph(figure=fig)