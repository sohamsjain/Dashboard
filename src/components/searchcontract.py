from datetime import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from src.app import *
from sqlalchemy import create_engine
import pandas as pd
from src.BaTMan import batman


df = pd.read_sql_table("contracts", db.engine)
observe_tickers = df.query("sectype!='OPT'")["symbol"].to_list()

ticker_dropdown_options = dict(
    observe=[dict(label=tk, value=tk) for tk in observe_tickers],
)

observe_ticker_dropdown = dcc.Dropdown(
    id="observe-ticker-dropdown",
    options=ticker_dropdown_options["observe"],
    value=None,
    placeholder="Ticker",
    className="m-3"

)

trade_ticker_dropdown = dcc.Dropdown(
    id="trade-ticker-dropdown",
    options=[],
    value=None,
    placeholder="Ticker",
    className="m-3"
)

exectype_radioitems = html.Div([
    dbc.RadioItems(
        id="exectype-radioitems",
        className="btn-group",
        labelClassName="btn btn-secondary",
        labelCheckedClassName="active",
        options=[
            dict(label=et, value=et) for et in ["Simple", "Conditional"]
        ],
        value="Simple",
    )],
    className="radio-group m-3"
)

trade_ticker_dropdown_div = html.Div(id="trade-ticker-dropdown-div")

entry_input = dcc.Input(
    id="entry-input",
    type="number",
    placeholder="Entry",
    className="m-3",
    style={"width": "90%"}
)

stoploss_input = dcc.Input(
    id="stoploss-input",
    type="number",
    placeholder="Stoploss",
    className="m-3",
    style={"width": "90%"}
)

target_input = dcc.Input(
    id="target-input",
    type="number",
    placeholder="Target",
    className="m-3",
    style={"width": "90%"}
)

size_input = dcc.Input(
    id="size-input",
    type="number",
    placeholder="Size",
    className="m-3",
    style={"width": "90%"}
)

size_div = html.Div(id="size-div")

submit_button = dbc.Button("Submit", color="light", className="m-3", id="submit-button", style={"width": "90%"})


toast = dbc.Toast(
            "Submitted Successfully",
            id="toast",
            header="New Xone",
            is_open=False,
            dismissable=True,
            duration=4000,
            icon="success",
            style={"position": "fixed", "bottom": 10, "right": 10, "width": 350},
        )

entry_form = html.Div(
    [exectype_radioitems, observe_ticker_dropdown, trade_ticker_dropdown_div, entry_input,
     stoploss_input, target_input, size_div, submit_button, toast])


@app.callback(
    Output(component_id="trade-ticker-dropdown-div", component_property="children"),
    Output(component_id="size-div", component_property="children"),
    Input(component_id="exectype-radioitems", component_property="value"),
)
def update_ticker_dropdown(exectype):
    if exectype is None:
        raise dash.exceptions.PreventUpdate
    if exectype == "Simple":
        return [], []
    if exectype == "Conditional":
        return trade_ticker_dropdown, size_input


@app.callback(
    Output(component_id="trade-ticker-dropdown", component_property="options"),
    Output(component_id="size-input", component_property="value"),
    Output(component_id="size-input", component_property="step"),
    Input(component_id="observe-ticker-dropdown", component_property="value"),
    State(component_id="exectype-radioitems", component_property="value")
)
def update_trade_ticker_options(observe_localSymbol, exectype):
    if exectype == "Conditional":
        if observe_localSymbol is None:
            raise dash.exceptions.PreventUpdate
        symbol = df.query(f"symbol=='{observe_localSymbol}'")["underlying"].values[0]
        cds = df.query(f"underlying=='{symbol}'")
        updated_list = cds["symbol"].to_list()
        lotsize = cds["lotsize"].values[-1]
        return [dict(label=tk, value=tk) for tk in updated_list], lotsize, lotsize


@app.callback(
    Output(component_id="target-input", component_property="value"),
    Output(component_id="submit-button", component_property="color"),
    Input(component_id="entry-input", component_property="value"),
    Input(component_id="stoploss-input", component_property="value"),

)
def update_trade_ticker_options(entry, stoploss):
    if entry and stoploss:
        risk = abs(entry - stoploss)
        if entry > stoploss:
            return entry + risk, "success"
        elif entry < stoploss:
            return entry - risk, "danger"
    return None, "light"


@app.callback(
    Output(component_id="exectype-radioitems", component_property="value"),
    Input(component_id="observe-ticker-dropdown", component_property="value"),
)
def update_trade_ticker_options(observe_ticker):
    if observe_ticker:
        sectype = df.query(f"symbol=='{observe_ticker}'")["sectype"].values[0]
        if sectype == "IND":
            return "Conditional"
    raise dash.exceptions.PreventUpdate


@app.callback(
    Output(component_id="observe-ticker-dropdown", component_property="value"),
    Output(component_id="trade-ticker-dropdown", component_property="value"),
    Output(component_id="entry-input", component_property="value"),
    Output(component_id="stoploss-input", component_property="value"),
    Output(component_id="toast", component_property="is_open"),
    Output(component_id="toast", component_property="children"),
    Input(component_id="submit-button", component_property="n_clicks"),
    State(component_id="exectype-radioitems", component_property="value"),
    State(component_id="observe-ticker-dropdown", component_property="value"),
    State(component_id="trade-ticker-dropdown", component_property="value"),
    State(component_id="entry-input", component_property="value"),
    State(component_id="stoploss-input", component_property="value"),
    State(component_id="target-input", component_property="value"),
    State(component_id="size-input", component_property="value"), prevent_initial_call=True
)
def submit(n, exec, observe, trade, entry, stoploss, target, size):
    if n:
        xone = dict(
            symbol=observe,
            entry=entry,
            stoploss=stoploss,
            target=target,
            children=[
                dict(
                    symbol=observe if exec == "Simple" else trade,
                    size=size
                )
            ]
        )
        response = batman.create(xone)
        return None, None, None, None, True, response
    raise dash.exceptions.PreventUpdate
