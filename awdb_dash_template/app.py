# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 10:59:51 2022

@author: Beau.Uriona
"""

from datetime import datetime as dt
import pandas as pd
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import dbs
from utils import get_plot_config, add_null_option
from views.controls import get_control_view

app = dbs.app
server = app.server

app.layout = dbc.Container(
    [
        dcc.Location(id="url"),
        html.Div(
            [
                html.P(
                    [
                        html.H4(dbs.APP_TITLE),
                        html.H5(
                            "Take a gander at this here nifty dashboard - Randy J. (I'm sure)",
                        ),
                    ],
                    style={"text-align": "center"},
                ),
            ],
            className="my-2",
        ),
        dbc.Row(
            [
                dbc.Col(get_control_view(), width=3),
                dbc.Col(
                    children=[
                        dbc.Tabs(
                            children=[
                                dbc.Tab(
                                    label="Westwide",
                                    children=[
                                        dbc.Row(
                                            dbc.Col(
                                                html.Div(
                                                    id="ww-map-div"
                                                )
                                            ),
                                        ),
                                        dbc.Row(
                                            dbc.Col(
                                                html.Div(
                                                    "west wide chart here", 
                                                    id="ww-chart"
                                                )
                                            ),
                                        ),
                                    ],
                                ),
                                dbc.Tab(
                                    label="Site",
                                    children=[
                                        dbc.Row(
                                            dbc.Col(
                                                html.Div(
                                                    "site map here",
                                                    id="site-map", className="p-2"
                                                ),
                                            ),
                                        ),
                                    ],
                                ),
                                dbc.Tab(
                                    label="Tabular",
                                    children=[
                                        dbc.Row(
                                            dbc.Col(
                                                children=[
                                                    html.Div(
                                                        id="datatable", 
                                                        children=["data table here"]
                                                    )
                                                ]
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            className="my-2",
        ),
    ],
    fluid=True,
)


def parse_url_args(arg_str):
    if not arg_str:
        return {}
    try:
        args = arg_str[1:].split("&")
        args = {i.split("=")[0]: i.split("=")[1] for i in args}
        return args
    except Exception as err:
        print(f"Error parsing url args, ignoring... - {err}")
        return {}


# @app.callback(
#     [
#         Output("response-station", "options"),
#     ],
#     [
#         Input("station-selector", "value"),
#     ],
#     [
#         State("station-selector", "value"),
#     ],
# )
# def function_dostuff(arg1, arg2):
    
#     return (
#         arg1
#     )



if __name__ == "__main__":

    import argparse

    cli_desc = """
    Run the SNOTEL Regression Tool locally for development
    """
    parser = argparse.ArgumentParser(description=cli_desc)
    parser.add_argument(
        "-V", "--version", help="show program version", action="store_true"
    )
    parser.add_argument("-d", "--debug", help="run in debug mode", action="store_true")
    parser.add_argument("--port", help="set port to deploy on", default=5000)
    args = parser.parse_args()

    app.run_server(
        port=args.port,
        debug=args.debug,
    )
