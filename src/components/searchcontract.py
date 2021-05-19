from datetime import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from src.app import app
from sqlalchemy import create_engine
import pandas as pd

conn = create_engine(r"sqlite:///C:\Users\PC2\PycharmProjects\Dashboard\contracts.db", echo=False)
df = pd.read_sql_table("Contracts", conn)
observe_tickers = df.query("sectype!='OPT'")["localSymbol"].to_list()
all_symbols = df.localSymbol.to_list()

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
    style={"width":"90%"}
)

stoploss_input = dcc.Input(
    id="stoploss-input",
    type="number",
    placeholder="Stoploss",
    className="m-3",
    style={"width":"90%"}
)

target_input = dcc.Input(
    id="target-input",
    type="number",
    placeholder="Target",
    className="m-3",
    style={"width":"90%"}
)

size_input = dcc.Input(
    id="size-input",
    type="number",
    placeholder="Size",
    className="m-3",
    style={"width":"90%"}
)

size_div = html.Div(id="size-div")

submit_button = dbc.Button("Submit", color="light", className="m-3", id="submit-button", style={"width":"90%"})

entry_form = html.Div(
    [exectype_radioitems, observe_ticker_dropdown, trade_ticker_dropdown_div, entry_input,
     stoploss_input, target_input, size_div, submit_button])


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
        symbol = df.query(f"localSymbol=='{observe_localSymbol}'")["symbol"].values[0]
        updated_list = df.query(f"symbol=='{symbol}'")["localSymbol"].to_list()
        return [dict(label=tk, value=tk) for tk in updated_list], 75, 75


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
    raise dash.exceptions.PreventUpdate


@app.callback(
    Output(component_id="exectype-radioitems", component_property="value"),
    Input(component_id="observe-ticker-dropdown", component_property="value"),
)
def update_trade_ticker_options(observe_ticker):
    if observe_ticker:
        sectype = df.query(f"localSymbol=='{observe_ticker}'")["sectype"].values[0]
        if sectype == "IND":
            return "Conditional"
    raise dash.exceptions.PreventUpdate