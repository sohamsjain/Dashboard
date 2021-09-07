from src.myapp import *


tickercomponent = dbc.FormGroup(
    [
        dbc.Label("Ticker", html_for="addchild-ticker-dropdown", style=labelstyle),
        dcc.Dropdown(
            id="addchild-ticker-dropdown",
            options=[],
            placeholder="Ticker",
            style=labelstyle
        ),
    ]
)

sizecomponent = dbc.FormGroup(
    [
        dbc.Label("Size", html_for="size-input", style=labelstyle),
        dbc.Input(type="number", id="size-input", placeholder="Size", style=labelstyle),
        dbc.FormText(id="size-formtext", style=textstyle, color="danger")
    ]
)

alertcomponent = dbc.Alert(id="addchild-form-alert", is_open=False, duration=4000, style=textstyle)


typecomponent = html.Div([
    dbc.RadioItems(
        id="childtype-radioitems",
        className="btn-group",
        labelClassName="btn btn-primary",
        labelCheckedClassName="active",
        options=[
            dict(label=each, value=each, color='primary') for each in ["Auto", "Buy", "Sell"]
        ],
        value="Auto",
    )],
    className="radio-group m-3"
)

storexoneid = dcc.Store(id="store-xoneid")

addchildform = dbc.Form(
    [
        tickercomponent, sizecomponent, alertcomponent, storexoneid
    ]
)

addchildmodal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.Label("Add New Child", style=labelstyle)
        ),
        dbc.ModalBody(
            [
                addchildform
            ]
        ),
        dbc.ModalFooter(
            [
                typecomponent,
                dbc.Button(
                    "Submit",
                    id=dict(object="addchild-form", component="submit-button"),
                    className="ml-auto",
                    n_clicks=0,
                    color="primary"
                )
            ]

        ),
    ],
    id="addchild-modal",
    scrollable=True,
    is_open=False
)