import dash
import dash_bootstrap_components as dbc

# 'https://codepen.io/chriddyp/pen/bWLwgP.css',
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server
