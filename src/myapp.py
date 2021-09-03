import dash
from dash.dependencies import Input, Output, State, MATCH, ALL
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash_daq.BooleanSwitch import BooleanSwitch
import dash_html_components as html
import pandas as pd

from src.models import Db, Xone, Child
from src.styles import *
from src.clientrequests import XoneRequests, ChildRequests

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

db = Db()