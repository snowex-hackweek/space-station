# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 15:54:26 2022

@author: Beau.Uriona
"""

import dash_leaflet as dl
from dash import dcc, html
import dash_bootstrap_components as dbc

MAPBOX_PREFIX = "https://api.mapbox.com/styles/v1/mapbox"
MAPBOX_TOKEN = "pk.eyJ1IjoiYmVhdXRhaCIsImEiOiJja3kyNWpldzcwaHgzMnBsYThzdWgzOG0xIn0.SpsS6_O1_oNfhaikt1Y2Kw"


def get_mapbox_layers():
    return {
        "Satellite": "satellite-streets-v11",
        "Street": "streets-v11",
        "Terrain": "outdoors-v11",
    }


def get_tile_layers(
    default_layer="Satellite", prefix=MAPBOX_PREFIX, token=MAPBOX_TOKEN
):
    tile_layers = []
    for label, style in get_mapbox_layers().items():
        layer_url = f"{prefix}/{style}/tiles/{{z}}/{{x}}/{{y}}?access_token={token}"
        checked = False
        if label == default_layer:
            checked = True
        base_layer = dl.BaseLayer(
            dl.TileLayer(url=layer_url, attribution="Mapbox"),
            name=label,
            checked=checked,
        )
        tile_layers.append(base_layer)
    return tile_layers


def make_minichart(site_data, site_id, width=300):
    return dl.Minichart(
        lat=site_data.lat,
        lon=site_data.lon,
        type="polar-radius",
        id="wind-chart",
        width=width,
        maxValues=30,
        # transitionTime=750
    )


def ww_map(df, height="90vh"):
   
    # mini_chart = make_minichart(site_data, site_id, width=200)
    markers = []
    for idx, row in df.iterrows():
        site_name = row.name
        marker = dl.Marker(
            position=[row.latitude, row.longitude],
            children=[
                dl.Tooltip(site_name),
                dl.Popup([html.H4(site_name), html.P("what do we want here?")]),
            ],
        )
        markers.append(marker)

    tile_layers = get_tile_layers()

    wind_map = dl.Map(
        dl.LayersControl(
            tile_layers
            + [
                # dl.Overlay(dl.LayerGroup(mini_chart), name="Wind", checked=True),
                dl.Overlay(dl.LayerGroup(markers), name="Site Info", checked=False),
            ],
        ),
        id="ww-map",
        style={
            "width": "100%",
            "height": height,
            "margin": "auto",
            "display": "block",
        },
        center=(site_data.lat, site_data.lon),
        zoom=12,
    )
    wind_data = dcc.Store(
        id=f"wind-data",
        data=get_wind_data(site_data, red_alarm, yellow_alarm, loop_len=loop_len),
    )
    return html.Div(
        [
            wind_data,
            wind_map,
        ]
    )