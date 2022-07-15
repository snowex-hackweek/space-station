# -*- coding: utf-8 -*-
"""
Created on Wed Jul 21 08:09:07 2021

@author: Beau.Uriona
"""

import sys
import json
from datetime import date
from datetime import datetime as dt
from os import path, makedirs
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from requests import get as r_get
# import ORM.awdb as awdb
# import ORM.snotel as snotel

THIS_DIR = path.dirname(path.abspath(__file__))
NETWORKS = ["SNTL", "SCAN", "SNTLT"]
DEFAULT_USER = 'beau.uriona'
DEFAULT_HOST = "nrcpboxiscprd3a.edc.ds1.usda.gov"
DEFAULT_IP = "10.203.20.88"
DEFAULT_PORT = "26023"

# START_DATE = 
# END_DATE = 
def get_awdb_config(key='beau.uriona'):
    with open('config.awdb', 'r') as cfg:
        config = json.load(cfg)
    return config.get(key, None)


def get_conn_str(config_key, db='snotel', use_ip=False):
    config = get_awdb_config(config_key)
    if config:
        driver = 'mssql+pymssql'
        user = config['user'].replace('@', '%40')
        password = config['password'].replace('@', '%40')
        host = DEFAULT_HOST
        ip = DEFAULT_IP
        if use_ip:
            host = ip
        port = DEFAULT_PORT
        connect_str = fr"{driver}://{user}:{password}@{host}:{port}/{db}"
        return connect_str
    else:
        return

conn_str = get_conn_str(config_key="beau.uriona", db='snotel', use_ip=True)

url = "https://www.nrcs.usda.gov/Internet/WCIS/sitedata/metadata/ALL/metadata.json"
meta = r_get(url)
if meta.ok:
    meta = meta.json()
else:
    print("Failed to get metadata...")
    sys.exit(1)
    
meta[:] = [i for i in meta if i["stationTriplet"].split(":")[-1] in NETWORKS]
meta = pd.DataFrame().from_dict(meta)
meta['id'] = meta['stationTriplet'].apply(lambda x: int(x.split(":")[0]))

sql_stmt = """
select count(*) as record_count, station_id as id, master_id as master from snot_sample 
  where sampled between '2021-12-01' and '2021-12-15' 
  --and station_id = 1098 
  and group_id = 1
  and master_id = 20
  group by station_id, master_id;
""".strip()

sql_stmt = """
select * from snot_sample 
  where sampled between '2021-12-15' and '2022-01-01' 
  and group_id = 1
  and master_id = 20
  --group by station_id, group_id, master_id
""".strip()

eng = create_engine(conn_str)
with eng.connect() as con:
    df = pd.read_sql(
        sql_stmt,
        con
    )

# df = df.join(meta, on="id", lsuffix='_snotel', rsuffix='_meta')
# df['percent_missing'] = round(100 - 100 * df['record_count'] / 337, 1)

df_groupby = df.copy()
df_groupby["hour"] = df_groupby['sampled'].dt.hour
df_gb = df_groupby.copy()
df_gb = df_gb.groupby(by=["hour", "station_id"], as_index=False).size()
df_gb.rename(columns={"size": "count"}, inplace=True)
df_limit = df_gb[df_gb["count"] < 12]
df_limit['hour'].value_counts()
df_limit['hour'].mode()
