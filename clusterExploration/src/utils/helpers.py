### Put helper functions here
import pandas as pd
from dash import html
import dash_ag_grid as dag

def generate_generic_DataTable(df, id_val, col_defs={}, exportable=False):
    col_defs = [{"field": col} for col in df.columns] if not col_defs else col_defs

    dag_datatable = html.Div(
        [
            dag.AgGrid(
                id=id_val,
                enableEnterpriseModules=True,
                className="ag-theme-alpine-dark",
                defaultColDef={
                    "filter": "agSetColumnFilter",
                    "editable": True,
                    # "flex": 1,
                    "filterParams": {"debounceMs": 2500},
                    "floatingFilter": True,
                    "sortable": True,
                    "resizable": True,
                },
                columnDefs=col_defs,
                rowData=df.to_dict("records"),
                dashGridOptions={"pagination": True, "paginationAutoPageSize": True},
                # columnSize="sizeToFit",
                csvExportParams={
                    "fileName": f"{id_val.replace('-', '_')}.csv",
                }
                if exportable
                else {},
                style={"height": "50vh"},
            ),
        ]
    )

    return dag_datatable





def load_dataset( csvFileName, options = None):
    ## Options would relate to column reformatting, type casting or whatever you feel like doing
    df = pd.read_csv(csvFileName)
    ## Do stuff here?
    return df


