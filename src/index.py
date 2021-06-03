import dash_html_components as html
import dash_bootstrap_components as dbc
from src.app import app
from src.components.searchcontract import *
from src.components.table import *


def serve_layout():
    return html.Div(children=[
    dbc.Row(children=[
        dbc.Col(children=[entry_form], width=3),
        dbc.Col(children=[xones, interval, children], width=9)
    ])
])

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(host="localhost")
