# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 18:06:00 2022

@author: Beau.Uriona
"""

import os
import json
import pickle
from datetime import date
from datetime import datetime

import rasterio
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from sqlalchemy.sql import func
from geoalchemy2.types import Raster
import geoalchemy2.functions as gfunc
from geoalchemy2.shape import from_shape
from metloom.pointdata import SnotelPointData

# Import the function to get connect to the db
from snowexsql.db import get_db
from snowexsql.conversions import query_to_pandas, raster_to_rasterio
from snowexsql.data import SiteData, LayerData, ImageData


BUFFER_IN_METERS = 10 * 1000  # 10km
SNOW_EX_GEOJSON_FILENAME = "snow_ex_all_stations.geojson"
REFRESH_SNOW_EX_GEOJSON = True
SNOWEX_DB_NAME = "snow:hackweek@db.snowexdata.org/snowex"
API_DOMAIN = "https://api.snowdata.info/"
ASO_PROXIMAL_SNTL = "622:CO:SNTL"
ASO_FLIGHT_DATES = [date(2020, 2, 2)]  # , date(2020, 2, 13))

def get_awdb_data(
    site_ids,
    element="WTEQ",
    sdate=datetime(1899, 10, 1),
    edate=datetime.now(),
    orient="records",
    server=API_DOMAIN,
    sesh=None,
):
    """
    Takes a list of site ids or a single site id and by default returns SWE period of record data as a single or list of dataframes,
    but user can pass args to modify data returned.

    Valid elements include WTEQ, SNWD, PREC, SMS, STO, TAVG
    site_id takes the form of a triplet made from <network_site_id>:<state_abbrv>:<network> where network is either SNTL or MNST
    """
    dfs = []
    return_single = False
    if not isinstance(site_ids, list):
        site_ids = [site_ids]
        return_single = True
    for site_id in site_ids:
        endpoint = "data/getDaily"
        date_args = f"sDate={sdate:%Y-%m-%d}&eDate={edate:%Y-%m-%d}"
        frmt_args = f"format=json&orient={orient}"
        all_args = f"?triplet={site_id}&{date_args}&element={element}&{frmt_args}"
        url = f"{server}{endpoint}{all_args}"
        print(
            f"getting data for {site_id} {element} starting {sdate:%Y-%m-%d} "
            f"and ending {edate:%Y-%m-%d}"
        )
        data_col_lbl = f"{site_id}" + ":" + f"{element}"
        if sesh:
            req = sesh.get(url)
        else:
            req = requests.get(url)
        if req.ok:
            df = pd.DataFrame.from_dict(req.json())
            df.columns = ["Date", data_col_lbl]
            df.set_index("Date", inplace=True)
        else:
            print("  No data returned!")
            df = (
                pd.DataFrame(
                    data=[{"Date": pd.NaT, data_col_lbl: np.nan}],
                )
                .set_index("Date")
                .dropna()
            )
        dfs.append(df)
    if return_single:
        return dfs[0]
    return dfs


def get_aso_depths(
    dt, snotel_code="622:CO:SNTL", crs=26912, buffer_dist=BUFFER_IN_METERS / 10
):
    """
    Args:
        dt: datetime or date object
        snotel_code: desired NRCS api station code
        crs: integer crs
        buffer_dist: buffer distance in same units as crs (default 1000 m)
    """
    # Pull in Snotel point
    sntl_point = SnotelPointData(snotel_code, "dummy name")
    geom = sntl_point.metadata
    geom = gpd.GeoSeries(geom).set_crs(4326).to_crs(crs).geometry.values[0]

    # grab a session
    engine, session = get_db(SNOWEX_DB_NAME)

    # Building a buffer which will give us a buffer object around our point
    buffer = session.query(
        gfunc.ST_SetSRID(gfunc.ST_Buffer(from_shape(geom), buffer_dist), crs)
    ).all()[0][0]

    # Grab the rasters, union them and convert them as tiff when done
    q = session.query(func.ST_AsTiff(func.ST_Union(ImageData.raster, type_=Raster)))

    # Only grab rasters that are the bare earth DEM from USGS
    q = q.filter(ImageData.type == "depth").filter(ImageData.observers == "ASO Inc.")
    q = q.filter(ImageData.date == dt)

    # And grab rasters touching the circle
    q = q.filter(gfunc.ST_Intersects(ImageData.raster, buffer))

    # Execute the query
    rasters = q.all()

    # Get the rasterio object of the raster
    dataset = raster_to_rasterio(session, rasters)[0]
    return dataset


def rasterio_to_df(dataset):
    data = dataset.read(1)
    data[data < 0] = np.nan
    data_shape = data.shape
    crs = dataset.crs
    cols, rows = np.meshgrid(np.arange(data_shape[0]), np.arange(data_shape[1]))
    xs, ys = rasterio.transform.xy(dataset.transform, rows, cols)

    xs = np.array([np.array(xi) for xi in xs])
    ys = np.array([np.array(yi) for yi in ys])
    values = data.flatten()
    points = gpd.points_from_xy(xs.flatten(), ys.flatten())
    df_depths = gpd.GeoDataFrame(geometry=points)
    df_depths["depth"] = values
    df_depths = df_depths.set_crs(crs)
    df_depths = df_depths.dropna()
    return df_depths


awdb_site_id = ASO_PROXIMAL_SNTL
gdfs_rasters = []
flight_dates = ASO_FLIGHT_DATES
for flight_date in flight_dates:
    print(f"Getting ASO data for {awdb_site_id} on {flight_date:%Y-%m-%d}")
    dataset = get_aso_depths(flight_date, snotel_code=awdb_site_id)
    gdf_depths = rasterio_to_df(dataset)
    gdf_depths = gdf_depths.to_crs(4326)
    gdf_depths["date"] = flight_date
    gdf_depths["instrument"] = "lidar"
    gdf_depths["awdb_id"] = awdb_site_id
    gdf_depths["snowex_pit_id"] = "n/a"
    gdf_depths["snowex_id"] = "GM Lidar"
    gdf_depths["swe_snowex"] = np.nan
    gdf_depths["depth"] = gdf_depths["depth"] * 1000
    gdfs_rasters.append(gdf_depths)


if REFRESH_SNOW_EX_GEOJSON or not os.path.isfile(SNOW_EX_GEOJSON_FILENAME):
    # Get the snow ex sites
    engine, session = get_db(SNOWEX_DB_NAME)
    qry = session.query(
        SiteData.site_name, SiteData.site_id, SiteData.latitude, SiteData.longitude
    )

    df_snow_ex = query_to_pandas(qry, engine).drop_duplicates(subset=["site_id"])
    gdf_snow_ex = gpd.GeoDataFrame(
        df_snow_ex,
        geometry=gpd.points_from_xy(df_snow_ex.longitude, df_snow_ex.latitude),
        crs=4326,
    )
    gdf_snow_ex.to_file(SNOW_EX_GEOJSON_FILENAME, driver="GeoJSON")
    # gdf_snow_ex.rename(columns={"geom": "geometry"}, inplace=True)
    session.close()
else:
    gdf_snow_ex = gpd.read_file(SNOW_EX_GEOJSON_FILENAME)

print(f"The CRS of the Snow Ex metadata is - {gdf_snow_ex.crs}")
gdf_snow_ex_buffer = gdf_snow_ex.to_crs(26912).buffer(BUFFER_IN_METERS).to_crs(4326)
snow_ex_bounds = gdf_snow_ex.to_crs(4326).total_bounds
print(f"The bounding box of the snow Ex sites is - {snow_ex_bounds}")
snow_ex_map = gdf_snow_ex_buffer.to_crs(4326).explore()
snow_ex_map = gdf_snow_ex.to_crs(4326).explore(m=snow_ex_map)


# Get SNOTEL Sites
AWDB_API_DOMAIN = "https://api.snowdata.info"
sntl_meta_url = f"{AWDB_API_DOMAIN}/stations/getMeta?network=SNTL&format=geojson"
msnt_meta_url = f"{AWDB_API_DOMAIN}/stations/getMeta?network=MSNT&format=geojson"
# Get the data and rename everything to match the snow ex columns
gdf_sntl = gpd.read_file(sntl_meta_url).rename(
    columns={"name": "site_name", "stationTriplet": "site_id"}
)
gdf_msnt = gpd.read_file(msnt_meta_url).rename(
    columns={"name": "site_name", "stationTriplet": "site_id"}
)
gdf_sntl = pd.concat([gdf_msnt, gdf_sntl])
gdf_sntl = gdf_sntl[gdf_sntl["beginDate"].dt.year <= 2017]
print(f"The CRS of the Snotel metadata is - {gdf_sntl.crs}, better change it")
gdf_sntl = gdf_sntl.to_crs(gdf_snow_ex.crs)
print(f"The CRS of the Snotel metadata is now - {gdf_sntl.crs}, all good!")
# Only keep the columns we care about... for now
gdf_sntl = gdf_sntl.drop(
    columns=[
        i for i in gdf_sntl.columns if i not in ["geometry", "site_id", "site_name"]
    ]
).set_geometry("geometry")
gdf_sntl_clipped = gdf_sntl.clip(gdf_snow_ex_buffer)
sntl_map = gdf_sntl_clipped.explore()
snow_ex_map = gdf_sntl_clipped.explore(m=snow_ex_map)
print(
    f"{len(gdf_sntl_clipped)} AWDB sites were found within "
    f"{BUFFER_IN_METERS / 1000:.0f} km of SnowEx Sites"
)
_ = [
    print(f'* {row["site_name"]} ({row["site_id"]})')
    for idx, row in gdf_sntl_clipped.sort_values("site_name").iterrows()
]
valid_triplets = list(set(gdf_sntl_clipped["site_id"]))

with requests.Session() as sesh:
    dfs_swe = get_awdb_data(
        site_ids=valid_triplets, element="WTEQ", sdate=datetime(2016, 10, 1), sesh=sesh
    )
    dfs_snwd = get_awdb_data(
        site_ids=valid_triplets, element="SNWD", sdate=datetime(2016, 10, 1), sesh=sesh
    )
df_all_swe_data = pd.concat(dfs_swe, axis=1)
df_all_snwd_data = pd.concat(dfs_snwd, axis=1)
df_all_awdb_data = pd.concat([df_all_swe_data, df_all_snwd_data], axis=1).fillna(np.nan)
df_all_awdb_data.index = pd.to_datetime(df_all_awdb_data.index)

gdf_all_flights = pd.concat(gdfs_rasters).rename(columns={"depth": "depth_snowex"})
date_idx = pd.to_datetime(gdf_all_flights["date"])
gdf_all_flights.drop(columns="date", inplace=True)
gdf_all_flights.index = date_idx
gdf_all_flights.index.name = "date"
sntl_point = (
    gdf_sntl_clipped[gdf_sntl_clipped["site_id"] == awdb_site_id]["geometry"]
    .to_crs(26912)
    .values[0]
)
gdf_all_flights["distance"] = (
    gdf_all_flights.to_crs(26912).distance(sntl_point).round(0)
)
gdf_all_flights = gdf_all_flights[gdf_all_flights["distance"] <= 1000]
gdf_awdb_site = df_all_awdb_data[[f"{awdb_site_id}:WTEQ", f"{awdb_site_id}:SNWD"]]
gdf_all_flights = gdf_all_flights.join((gdf_awdb_site / 0.0393701).round(0)).rename(
    columns={f"{awdb_site_id}:WTEQ": "swe_awdb", f"{awdb_site_id}:SNWD": "depth_awdb"}
)

engine, session = get_db(SNOWEX_DB_NAME)
use_cols = ("site_id", "date", "pit_id", "value", "geometry", "depth", "instrument")
obj = {}
data_dfs = []
for awdb_site_id in valid_triplets[4:]:
    gdf_awdb_site_buffer = (
        gdf_sntl[gdf_sntl["site_id"] == awdb_site_id]
        .to_crs(26912)
        .buffer(BUFFER_IN_METERS)
        .to_crs(4326)
    )
    gdf_snow_ex_inside = gdf_snow_ex.clip(gdf_awdb_site_buffer)
    snow_ex_site_list = gdf_snow_ex_inside["site_id"].tolist()
    awdb_site_name = gdf_sntl[gdf_sntl["site_id"] == awdb_site_id]["site_name"].values[
        0
    ]
    print(
        f"The AWDB site: {awdb_site_name} has {len(snow_ex_site_list)} SnowEx pits within "
        f"{BUFFER_IN_METERS / 1000:.0f} km ({', '.join(snow_ex_site_list)})."
    )

    qry = (
        session.query(LayerData)
        .filter(LayerData.site_id.in_(snow_ex_site_list))
        .filter(LayerData.type == "density")
    )
    df_snow_ex_data = query_to_pandas(qry, engine)
    gdf_snow_ex_data = gpd.GeoDataFrame(
        df_snow_ex_data,
        geometry=gpd.points_from_xy(
            df_snow_ex_data.longitude, df_snow_ex_data.latitude
        ),
        crs=4326,
    )
    gdf_snow_ex_data.drop(
        columns=[i for i in df_snow_ex_data.columns if i not in use_cols], inplace=True
    )
    gdf_snow_ex_data.loc[:, "value"] = gdf_snow_ex_data["value"].astype(float)
    gdf_snow_ex_data.index = pd.to_datetime(gdf_snow_ex_data["date"])
    df_grp_by = gdf_snow_ex_data.groupby(by="pit_id")
    df_date = df_grp_by["date"].first()
    df_bulk_density = df_grp_by["value"].mean() / 1000  # convert kg/m^3
    df_depth = df_grp_by["depth"].max() * 10  # convert cm to mm
    df_swe = df_depth * df_bulk_density
    df_pit_id = df_grp_by["pit_id"].first()
    df_values = gpd.GeoDataFrame(
        data={"swe_snowex": df_swe.round(0), "depth_snowex": df_depth, "date": df_date}
    )  # .set_geometry("geometry")
    df_values.index = df_pit_id.values  # pd.to_datetime(df_values["date"])
    gdf_snow_ex_data.drop(columns="date", inplace=True)
    df_pit_data = df_grp_by.first().drop(columns=["depth", "value"])
    df_combined = df_pit_data.join(df_values)
    df_awdb_site = df_all_awdb_data[[f"{awdb_site_id}:WTEQ", f"{awdb_site_id}:SNWD"]]
    df_combined = df_combined.reset_index()
    df_combined.index = df_date
    df_combined = df_combined.join((df_awdb_site / 0.0393701).round(0)).rename(
        columns={
            f"{awdb_site_id}:WTEQ": "swe_awdb",
            f"{awdb_site_id}:SNWD": "depth_awdb",
        }
    )

    df_combined["awdb_id"] = awdb_site_id
    df_combined.set_crs(4326, inplace=True)
    sntl_point = (
        gdf_sntl_clipped[gdf_sntl_clipped["site_id"] == awdb_site_id]["geometry"]
        .to_crs(26912)
        .values[0]
    )
    df_combined["distance"] = df_combined.to_crs(26912).distance(sntl_point).round(0)
    df_combined["instrument"] = "manual"
    df_combined.rename(
        columns={"site_id": "snowex_id", "pit_id": "snowex_pit_id"}, inplace=True
    )
    data_dfs.append(df_combined)

gdf_all_data = pd.concat(data_dfs + [gdf_all_flights])
obj["data"] = gdf_all_data.to_crs(4326)
obj["meta"] = {
    "awdb": gdf_sntl_clipped.to_crs(4326),
    "snowex": gdf_snow_ex.to_crs(4326),
}

with open("one_obj_to_rule_them_all.pkl", "wb") as p:
    pickle.dump(obj, p)

with open("one_obj_to_rule_them_all.json", "w") as j:
    json.dump(
        {
            "data": json.loads(
                gdf_all_data.to_crs(4326).astype({"date": str}).to_json()
            ),
            "meta": {
                "awdb": json.loads(gdf_sntl_clipped.to_crs(4326).to_json()),
                "snowex": json.loads(gdf_snow_ex.to_crs(4326).to_json()),
            },
        },
        j,
        indent=4,
    )
