import dash
import dash_bootstrap_components as dbc
from dash_daq.BooleanSwitch import BooleanSwitch
import dash_html_components as html
from dash.dependencies import Input, Output, State


# 'https://codepen.io/chriddyp/pen/bWLwgP.css',
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server


def make_item(i):
    # we use this function to make the example items to avoid code duplication
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H2(
                    [dbc.Button(
                        [f"Banknifty #{i}",
                         dbc.Badge("4", color="light", className="ml-1")],
                        style={
                            'background-color': '#5B0F00' if i % 2 == 0 else '#274E13',
                            'color': '#ffffff',
                            'border': '1px black solid',
                        },
                        id=f"group-{i}-toggle",
                        n_clicks=0,
                        className="m-3"
                    ),
                    dbc.Label("Entry", className='m-3', color="white"),
                    dbc.Label("Stoploss", className='m-3', color="pink"),
                    dbc.Label("Target", className='m-3', color="green"),
                    dbc.Label("Status", className='m-3', color="white"),
                    dbc.Label("Entry Time", className='m-3', color="white"),
                    dbc.Label("Exit Time", className='m-3', color="white"),
                    dbc.Label("Pnl", className='m-3', color="green"),
                    dbc.Button([f"Force Entry #{i}",
                         dbc.Badge("3", color="light", className="ml-1")],
                               style={
                                   'background-color': '#5B0F00' if i % 2 == 0 else '#274E13',
                                   'color': '#ffffff',
                                   'border': '1px black solid',
                               },
                               id=f"force-{i}-toggle",
                               n_clicks=0,
                               className="m-3"
                               ),
                    BooleanSwitch(on=True, color='blue')
                    ]
                ),
                style={
                    'background-color': '#434343',
                },
            ),
            dbc.Collapse(
                dbc.CardBody([dbc.CardHeader(
                html.H2(
                    [dbc.Button(
                        [f"Banknifty 35000 CE#{i}",
                         dbc.Badge("4", color="light", className="m-1")],
                        style={
                            'background-color': '#5B0F00' if i % 2 == 0 else '#274E13',
                            'color': '#ffffff',
                            'border': '1px black solid',
                        },
                        id=f"child-{i}-toggle",
                        n_clicks=0,
                        className="m-31"
                    ),
                    dbc.Label("Status", className='m-3', color="white"),
                    dbc.Label("Qty", className='m-3', color="white"),
                    dbc.Label("Pnl", className='m-3', color="green"),
                    BooleanSwitch(on=True, color='blue')]
                ),
                style={
                    'background-color': '#434343',
                },
            ),
                dbc.Button("Modify", color="primary", className='m-3')],
                             className='mx-3 mb-3',
                             style={
                                 'background-color': '#666666',
                                },
                             ),
                id=f"collapse-{i}",
                is_open=False,
                style={
                    'background-color': '#434343'
                }
            ),
        ]
    )


accordion = html.Div(
    [make_item(1), make_item(2), make_item(3)],
    className="accordion m-3",
    style={
        'background-color': '#000000',
    }
)

PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(type="search", placeholder="Search")),
        dbc.Col(
            dbc.Button(
                "Create", color="primary", className="m-3", n_clicks=0
            ),
            width="auto",
        ),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                    dbc.Col(dbc.NavbarBrand("Swayam Capital", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
            href="#",
        ),
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(
            search_bar, id="navbar-collapse", navbar=True, is_open=False
        ),
    ],
    color="dark",
    dark=True,
)

fullpage = html.Div(
    [navbar, accordion]
)


@app.callback(
    [Output(f"collapse-{i}", "is_open") for i in range(1, 4)],
    [Input(f"group-{i}-toggle", "n_clicks") for i in range(1, 4)],
    [State(f"collapse-{i}", "is_open") for i in range(1, 4)],
)
def toggle_accordion(n1, n2, n3, is_open1, is_open2, is_open3):
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, False, False
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "group-1-toggle" and n1:
        return not is_open1, False, False
    elif button_id == "group-2-toggle" and n2:
        return False, not is_open2, False
    elif button_id == "group-3-toggle" and n3:
        return False, False, not is_open3
    return False, False, False


def serve_layout():
    return fullpage


app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)
