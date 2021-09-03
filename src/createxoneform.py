from src.myapp import *
import src.globalvars as gvars

tickercomponent = dbc.FormGroup(
    [
        dbc.Label("Ticker", html_for="createxone-ticker-dropdown", style=labelstyle),
        dcc.Dropdown(
            id="createxone-ticker-dropdown",
            placeholder="Ticker",
            options=[
                dict(label=tk, value=tk) for tk in gvars.tickers
            ],
            style=labelstyle
        ),
    ]
)

entrycomponent = dbc.FormGroup(
    [
        dbc.Label("Entry", html_for="entry-input", style=labelstyle),
        dbc.Input(type="number", id="entry-input", placeholder="Entry", style=labelstyle, min=0),
        dbc.FormText(id="entry-formtext", style=textstyle, color="danger")
    ]
)

stoplosscomponent = dbc.FormGroup(
    [
        dbc.Label("Stoploss", html_for="stoploss-input", style=labelstyle),
        dbc.Input(type="number", id="stoploss-input", placeholder="Stoploss", style=labelstyle, min=0),
        dbc.FormText(id="stoploss-formtext", style=textstyle, color="danger"),
    ]
)

targetcomponent = dbc.FormGroup(
    [
        dbc.Label("Target", html_for="target-input", style=labelstyle),
        dbc.Input(type="number", id="target-input", placeholder="Target", style=labelstyle, min=0),
        dbc.FormText(id="target-formtext", style=textstyle, color="danger")
    ]
)

alertcomponent = dbc.Alert(id="createxone-form-alert", is_open=False, duration=4000, style=textstyle)

createxoneform = dbc.Form(
    [
        tickercomponent, entrycomponent, stoplosscomponent, targetcomponent, alertcomponent
    ]
)

createxonemodal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.Label("Create New Xone", style=labelstyle)
        ),
        dbc.ModalBody(
            [
                createxoneform
            ]
        ),
        dbc.ModalFooter(
            [
                dbc.Label(
                    f"Autonomous",
                    style=labelstyle,
                ),
                BooleanSwitch(
                    id=f"createxone-autonomous-switch",
                    on=True,
                    color="green",
                ),
                dbc.Button(
                    "Submit",
                    id="createxone-form-submit-button",
                    className="ml-auto",
                    n_clicks=0,
                    color="primary"
                )
            ]

        ),
    ],
    id="createxone-modal",
    scrollable=True,
    is_open=False,
)
