# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 18:06:00 2022

@author: Beau.Uriona
"""

from requests import Session
import geopandas as gpd
import pandas as pd

# Import the function to get connect to the db
from snowexsql.db import get_db
from snowexsql.data import SiteData, PointData, LayerData, ImageData

# This is what you will use for all of hackweek to access the db
SNOWEX_DB_NAME = 'snow:hackweek@db.snowexdata.org/snowex'
AWDB_API_DOMAIN = "https://api.snowdata.info"
from snowexsql.conversions import query_to_geopandas

# Grab a session
engine, session = get_db(SNOWEX_DB_NAME)

qry = session.query(SiteData.site_name, SiteData.site_id, SiteData.geom).limit(10000)

gdf_snow_ex = query_to_geopandas(qry, engine).drop_duplicates(subset=["site_name"]).rename(columns={"geom": "geometry"})
print(gdf_snow_ex.crs)
gdf_snow_ex_buffer = gdf_snow_ex.buffer(0.5)
gdf_snow_ex_buffer.explore("site_name")
snow_ex_bounds = gdf_snow_ex.total_bounds

sntl_meta_url = f"{AWDB_API_DOMAIN}/stations/getMeta?network=SNTL&format=geojson"

gdf_sntl = gpd.read_file(sntl_meta_url).rename(
    columns={"name": "site_name", "siteTriplet": "site_id"}
)
gdf_sntl = gdf_sntl.to_crs(26912)
gdf_sntl = gdf_sntl.drop(
    columns=[i for i in gdf_sntl.columns if i not in ["geometry", "siteTriplet", "name"]]
)
gdf_sntl_buffer = gdf_sntl.buffer(0.5)
sntl_bounds = gdf_sntl.total_bounds

gdf_all = pd.concat([gdf_sntl, gdf_snow_ex])
gdf_all_buffer = gdf_all.buffer(0.5)
all_bounds = gdf_all.total_bounds