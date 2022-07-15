#!./.venv/bin/python
# coding: utf-8
"""
Created on Wed Nov  3 11:01:42 2021

@author: Beau.Uriona
"""
from datetime import timedelta
from os import path, getenv
from functools import reduce

import requests
import pandas as pd
from requests_cache import CachedSession


NULL_OPTION = {"label": "", "value": None}
THIS_DIR = path.dirname(path.realpath(__file__))
DB_DIR = path.join(THIS_DIR, "dbs")
CACHE_PATH = getenv("CACHE_PATH", path.join(DB_DIR, ".cache.db"))
CACHE_REFRESH = timedelta(hours=12)
CACHE_ARGS = {
    "cache_name": CACHE_PATH,
    "backend": "sqlite",
    "expire_after": CACHE_REFRESH,
}


def add_null_option(options=None):
    if options:
        options.insert(0, NULL_OPTION)
        return options
    return [NULL_OPTION]


def get_single(stationtriplet, element, s_date, e_date, orient, sesh=None):
    server = "http://nrcscix0147.edc.ds1.usda.gov:8041"
    #server = "https://api.snowdata.info"
    endpoint = "/data/getDaily"
    date_args = f"s_date={s_date}&e_date={e_date}"
    frmt_args = f"format=json&orient={orient}"
    all_args = f"?triplet={stationtriplet}&{date_args}&element={element}&{frmt_args}"
    url = f"{server}{endpoint}{all_args}"
    print(f"getting data for {url}")
    if sesh:
        req = sesh.get(url)
    else:
        req = requests.get(url)
    if req.ok:
        df = pd.DataFrame.from_dict(req.json())
    df.columns = ["Date", f"{stationtriplet}" + "(" + f"{element}" + ")"]
    df.set_index("Date", inplace=True)

    return df


def get_data(stationparameter_pairs, s_date, e_date, orient="records"):

    with CachedSession(**CACHE_ARGS) as sesh:
        try:
            data = reduce(
                lambda left, right: pd.merge(
                    left, right, left_index=True, right_index=True, how="outer"
                ),
                [
                    get_single(
                        stationtriplet=i[0],
                        element=i[1],
                        s_date=s_date,
                        e_date=e_date,
                        orient=orient,
                        sesh=sesh,
                    )
                    for i in stationparameter_pairs
                ],
            )

            return data

        except KeyError as err:
            print(f"KeyError occurred. - {err}")


def get_plot_config(img_filename="nrcs_chart.png"):
    return {
        "modeBarButtonsToRemove": ["sendDataToCloud", "lasso2d", "select2d"],
        "showAxisDragHandles": True,
        "showAxisRangeEntryBoxes": True,
        "displaylogo": False,
        "toImageButtonOptions": {
            "filename": img_filename,
            "width": 1200,
            "height": 700,
        },
        # 'scrollZoom': False,
        "modeBarButtonsToAdd": [
            "drawline",
            "drawopenpath",
            "drawclosedpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
            "drawtext",
        ],
    }


if __name__ == "__main__":
    print("I do nothing, just non dynamic components that take up space...")
