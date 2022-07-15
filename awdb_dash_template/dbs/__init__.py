# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from datetime import datetime
import dash

# from auth import basic_auth
from flask_sqlalchemy import SQLAlchemy
import dash_bootstrap_components as dbc

DB_DIR = os.path.dirname(os.path.realpath(__file__))
APP_DIR = os.path.dirname(DB_DIR)
APP_TITLE = "GOES Diagnostics Tool"
USE_AUTH = os.getenv("USE_AUTH", False)
AUTH_USER = os.getenv("AUTH_USER", "user")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "snotel")

DEFAULT_USER = 'beau.uriona'
DEFAULT_HOST = "nrcpboxiscprd3a.edc.ds1.usda.gov"
DEFAULT_IP = "10.203.20.88"
DEFAULT_PORT = "26023"


def get_awdb_config(key='beau.uriona'):
    config_path = os.path.join(DB_DIR, 'config.awdb')
    with open(config_path, 'r') as cfg:
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


def create_app(config_key=DEFAULT_USER):  # use_auth=USE_AUTH):
    assets_path = Path(APP_DIR, "assets")
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.YETI],
        update_title="Updating...",
        suppress_callback_exceptions=True,
        assets_folder=assets_path,
    )
    app.title = APP_TITLE
    # if use_auth:
    #     print(f"Using basic auth - env var USE_AUTH = {use_auth}")
    #     basic_auth.BasicAuth(app, {AUTH_USER: AUTH_PASSWORD})
    # meta_db_path = Path(DB_DIR, "meta.db")
    # meta_db_con_str = f"sqlite:///{meta_db_path.as_posix()}"
    app.server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # app.server.config["SQLALCHEMY_DATABASE_URI"] = meta_db_con_str
    app.server.config["SQLALCHEMY_BINDS"] = {
        "snotel": get_conn_str(config_key, db="snotel"),
        "awdb" : get_conn_str(config_key, db="awdb")
    }

    return app

app = create_app()
db = SQLAlchemy(app.server)
# db.reflect()

if __name__ == "__main__":

    print("Creates app and dbs")
    
