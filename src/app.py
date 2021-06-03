import dash
import dash_bootstrap_components as dbc
from src.BaTMan import batman
from src.models import *


# 'https://codepen.io/chriddyp/pen/bWLwgP.css',
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

db = Db()
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server
