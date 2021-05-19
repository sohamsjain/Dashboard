import dash_html_components as html
import dash_bootstrap_components as dbc
from src.app import app
from src.components.searchcontract import entry_form

# app.layout = entry_form

app.layout = html.Div(children=[
    dbc.Row(children=[
        dbc.Col(children=[entry_form], width=3),
        dbc.Col(children=[], width=9)
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
