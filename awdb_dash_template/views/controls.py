# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 08:09:07 2021

@author: Beau.Uriona
"""

from datetime import date
from dateutil.relativedelta import relativedelta

from dash import dcc, html
import dash_bootstrap_components as dbc

from views.static import tidbits

DEFAULT_DAYS_BACK = 7
DEFAULT_START = date.today() - relativedelta(days=DEFAULT_DAYS_BACK)
DEFAULT_END = date.today()

SELECT_OPTIONS = [
    {"label": "Something", "value": "something"},
]

def get_initial_dates(start=DEFAULT_START, end=DEFAULT_END):
    return (start, end)

def get_control_view(initial_dates=get_initial_dates()):
    return (
        dbc.Card(
            id="input-card",
            className="p-1",
            children=[
                dbc.Form(
                    id="input-form",
                    children=[
                        html.Div(
                            children=[
                                dbc.Label(
                                    "Placeholder:",
                                    html_for="slider",
                                ),
                                dcc.Slider(
                                    id="slider",
                                    min=0,
                                    max=100,
                                    step=10,
                                    value=10,
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": True,
                                    },
                                    className="my-1",
                                ),
                                dbc.Label(
                                    "Placeholder:",
                                    html_for="dropdown",
                                ),
                                dcc.Dropdown(
                                    id="dropdown",
                                    options=[],
                                    value="",
                                    placeholder="Select something",
                                ),
                                dbc.Select(
                                    id="select1",
                                    options=SELECT_OPTIONS,
                                    value="something",
                                    placeholder="Select something",
                                ),
                            ],
                            className="m-2",
                        ),
                        html.Div(
                            children=[
                                dbc.Label(
                                    "Placeholder:",
                                    html_for="radio",
                                ),
                                dbc.RadioItems(
                                    options=[
                                        {"label": "This one", "value": "this"},
                                        {"label": "That one", "value": "that"},
                                    ],
                                    value="this",
                                    id="radio",
                                    inline=True,
                                ),
                                dbc.Select(
                                    id="select2",
                                    options=SELECT_OPTIONS,
                                    value="something",
                                    placeholder="Select something",
                                ),
                                dbc.Select(
                                    id="select3",
                                    options=SELECT_OPTIONS,
                                    value="something",
                                    placeholder="Select something",
                                ),
                            ],
                            className="m-2",
                        ),
                        html.Div(
                            children=[
                                dbc.Label(
                                    "Placeholder",
                                    html_for="date-pickers",
                                ),
                                dbc.InputGroup(
                                    id="date-pickers",
                                    children=[
                                        dcc.DatePickerSingle(
                                            id="sdate-picker",
                                            min_date_allowed=date(1950, 10, 1),
                                            max_date_allowed=date.today(),
                                            date=get_initial_dates()[0],
                                        ),
                                        dcc.DatePickerSingle(
                                            id="edate-picker",
                                            min_date_allowed=date(1950, 10, 1),
                                            max_date_allowed=date.today(),
                                            date=get_initial_dates()[1],
                                        ),
                                    ],
                                    className="m-2",
                                ),
                                dbc.Label(
                                    "Placeholder:",
                                    html_for="submit-button",
                                ),
                                dbc.Button(
                                    id="submit-button",
                                    children="Do thing",
                                    color="secondary",
                                    className="m-2"
                                ),
                            ],
                            className="m-2",
                        ),
                        html.Div(html.Pre(id="text-box", children=[])),
                        html.Details(children=tidbits, className="my-2"),
                    ],
                )
            ],
        ),
    )


if __name__ == "__main__":
    print("I do nothing, just dynamic components that take up space...")
