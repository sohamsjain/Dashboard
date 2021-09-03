from src.myapp import *
from src.util import XoneStatus, XoneType, ChildType
from src.createxoneform import createxonemodal
from src.addchildform import addchildmodal
import src.globalvars as gvars


def createchildcomponents(child):
    child.isbuy = True if child.type == ChildType.BUY else False
    symbolstyle = {
        'background-color': 'green' if child.isbuy else 'red',
        'color': '#ffffff',
        'border': '1px black solid',
        'font-size': '16px'
    }

    child.symbolbutton = dbc.Button(
        child.symbol,
        id=dict(object="child", component="symbol-button", id=child.id),
        style=symbolstyle,
        block=True
    )

    child.statusdiv = html.Div(child.status.capitalize(),
                               id=dict(object="child", component="status-div", id=child.id),
                               className=m3,
                               style=StyleDefault[child.status])

    child.sizediv = html.Div(child.size,
                             id=dict(object="child", component="size-div", id=child.id),
                             className=m3,
                             style=StyleDefault[child.status])

    child.sizediv = html.Div(child.sizediv, id=f"child-{child.id}-size-div")

    child.size_popover_children = [
        dbc.PopoverHeader("Modify Size", style={'font-size': '16px'}),
        dbc.PopoverBody(
            [
                dcc.Input(
                    id=dict(object="child", component="size-modify-input", id=child.id),
                    className=my2,
                    type="number",
                    value=child.size,
                    step=child.contract.lotsize,
                    min=child.contract.lotsize
                ),
                dbc.Button("Modify", color="primary", block=True,
                           id=dict(object="child", component="size-modify-button", id=child.id))
            ],
            style={'font-size': '12px'}),
    ]

    child.size_popover = dbc.Popover(
        child.size_popover_children,
        id=dict(object="child", component="size-popover", id=child.id),
        target=f"child-{child.id}-size-div",
        trigger="legacy",
        placement="bottom"
    )

    child.filleddiv = html.Div(child.filled,
                               id=dict(object="child", component="filled-div", id=child.id),
                               className=m3,
                               style=StyleDefault[child.status])
    child.lastpricediv = html.Div(child.lastprice,
                                  id=dict(object="child", component="lastprice-div", id=child.id),
                                  className=m3,
                                  style=StyleDefault[child.status])
    child.pnldiv = html.Div(child.pnl, id=dict(object="child", component="pnl-div", id=child.id),
                            className=m3, style=StyleDefault[child.status])

    child.deletebutton = dbc.Button(
        "Delete Child",
        id=dict(object="child", component="delete-button", id=child.id, xoneid=child.xone.id),
        color="danger",
        block=True,
        size="sm",
        disabled=False
    )

    child.interval = dcc.Interval(
        id=dict(object="child", component="interval", id=child.id),
        interval=1000 * 3,
        n_intervals=0,
    )

    child.cardheader = dbc.CardHeader(
        [
            dbc.Row(
                [
                    dbc.Col(child.symbolbutton),
                    dbc.Col(child.statusdiv),
                    dbc.Col([child.sizediv, child.size_popover]),
                    dbc.Col(child.filleddiv),
                    dbc.Col(child.lastpricediv),
                    dbc.Col(child.pnldiv),
                    dbc.Col(child.deletebutton, width=1, align="center")
                ],
                align="center"
            )
        ]
    )

    childcomponent = html.Div([child.cardheader, child.interval],
                              id=dict(object="child", component="component", id=child.id))

    return childcomponent


def createxonecomponents(xone):

    global childcomponentsbyxoneid

    xone.isbullish = True if xone.type == XoneType.BULLISH else False

    symbolstyle = {
        'background-color': 'green' if xone.isbullish else 'red',
        'color': '#ffffff',
        'border': '1px black solid',
        'font-size': '16px'
    }

    xone.symbolbutton = dbc.Button(
        xone.symbol,
        id=dict(object="xone", component="symbol-button", id=xone.id),
        style=symbolstyle,
        block=True,
    )

    xone.entrydiv = html.Div(
        xone.entry,
        id=dict(object="xone", component="entry-div", id=xone.id),
        className=m3,
        style=Styles.Entry[xone.status],
    )

    xone.entrydiv = html.Div(xone.entrydiv, id=f"xone-{xone.id}-entry-div")

    xone.entry_popover_children = [
        dbc.PopoverHeader("Modify Entry", style={'font-size': '16px'}),
        dbc.PopoverBody(
            [
                dcc.Input(
                    id=dict(object="xone", component="entry-modify-input", id=xone.id),
                    className=my2,
                    type="number",
                    value=xone.entry
                ),
                dbc.Button("Modify",
                           color="primary",
                           block=True,
                           id=dict(object="xone", component="entry-modify-button", id=xone.id))
            ],
            style={'font-size': '12px'}),
    ]

    xone.entry_popover = dbc.Popover(
        xone.entry_popover_children,
        id=dict(object="xone", component="entry-popover", id=xone.id),
        target=f"xone-{xone.id}-entry-div",
        trigger="legacy",
        placement="bottom"
    )

    xone.stoplossdiv = html.Div(
        xone.stoploss,
        id=dict(object="xone", component="stoploss-div", id=xone.id),
        className=m3,
        style=Styles.Stoploss[xone.status])

    xone.stoplossdiv = html.Div(xone.stoplossdiv, id=f"xone-{xone.id}-stoploss-div")

    xone.stoploss_popover_children = [
        dbc.PopoverHeader("Modify Stoploss", style={'font-size': '16px'}),
        dbc.PopoverBody(
            [
                dcc.Input(
                    id=dict(object="xone", component="stoploss-modify-input", id=xone.id),
                    className=my2,
                    type="number",
                    value=xone.stoploss
                ),
                dbc.Button("Modify",
                           color="primary",
                           block=True,
                           id=dict(object="xone", component="stoploss-modify-button", id=xone.id))
            ],
            style={'font-size': '12px'}),
    ]

    xone.stoploss_popover = dbc.Popover(
        xone.stoploss_popover_children,
        id=dict(object="xone", component="stoploss-popover", id=xone.id),
        target=f"xone-{xone.id}-stoploss-div",
        trigger="legacy",
        placement="bottom"
    )

    xone.targetdiv = html.Div(
        xone.target,
        id=dict(object="xone", component="target-div", id=xone.id),
        className=m3,
        style=Styles.Target[xone.status])

    xone.targetdiv = html.Div(xone.targetdiv, id=f"xone-{xone.id}-target-div")

    xone.target_popover_children = [
        dbc.PopoverHeader("Modify Target", style={'font-size': '16px'}),
        dbc.PopoverBody(
            [
                dcc.Input(
                    id=dict(object="xone", component="target-modify-input", id=xone.id),
                    className=my2,
                    type="number",
                    value=xone.target
                ),
                dbc.Button("Modify",
                           color="primary",
                           block=True,
                           id=dict(object="xone", component="target-modify-button", id=xone.id))
            ],
            style={'font-size': '12px'}),
    ]

    xone.target_popover = dbc.Popover(
        xone.target_popover_children,
        id=dict(object="xone", component="target-popover", id=xone.id),
        target=f"xone-{xone.id}-target-div",
        trigger="legacy",
        placement="bottom"
    )

    xone.statusdiv = html.Div(
        xone.status.capitalize(),
        id=dict(object="xone", component="status-div", id=xone.id),
        className=m3,
        style=StyleDefault[xone.status])

    xone.lastpricediv = html.Div(
        xone.lastprice,
        id=dict(object="xone", component="lastprice-div", id=xone.id),
        className=m3,
        style=StyleDefault[xone.status])

    xone.pnldiv = html.Div(xone.pnl,
                           id=dict(object="xone", component="pnl-div", id=xone.id),
                           className=m3,
                           style=StyleDefault[xone.status])

    forcedisabled, forcecount = True, 0
    if xone.status in XoneStatus.PENDING:
        if not xone.forced_entry:
            forcedisabled, forcecount = False, 3
    elif xone.status in XoneStatus.OPEN:
        if not xone.forced_exit:
            forcedisabled, forcecount = False, 3

    xone.forcebutton = dbc.Button(
        [
            "Force",
            dbc.Badge(forcecount,
                      id=dict(object="xone", component="force-badge", id=xone.id))
        ],

        id=dict(object="xone", component="force-button", id=xone.id),
        style=StyleForce[xone.status],
        className=m3,
        block=True,
        size="sm",
        disabled=forcedisabled
    )

    xone.autonomousswitch = BooleanSwitch(
        id=dict(object="xone", component="autonomous-switch", id=xone.id),
        on=xone.autonomous,
        color="green",
        label="Autonomous",
        labelPosition="top"
    )

    xone.addchildbutton = dbc.Button(
        "Add Child",
        id=dict(object="xone", component="addchild-button", id=xone.id),
        color="primary",
        className=m3
    )

    xone.deletexonebutton = dbc.Button(
        "Delete Xone",
        id=dict(object="xone", component="delete-button", id=xone.id),
        color="danger",
        className=m3
    )

    xone.interval = dcc.Interval(
        id=dict(object="xone", component="interval", id=xone.id),
        interval=1000 * 3,
        n_intervals=0,
    )

    xone.store = dcc.Store(id=dict(object="xone", component="store", id=xone.id), data=xone.contract.underlying)

    gvars.childcomponentsbyxoneid.update({xone.id: [createchildcomponents(child) for child in xone.children]})

    xone.card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(xone.symbolbutton),
                            dbc.Col([xone.entrydiv, xone.entry_popover]),
                            dbc.Col([xone.stoplossdiv, xone.stoploss_popover]),
                            dbc.Col([xone.targetdiv, xone.target_popover]),
                            dbc.Col(xone.statusdiv),
                            dbc.Col(xone.lastpricediv),
                            dbc.Col(xone.pnldiv),
                            dbc.Col(xone.forcebutton),
                            dbc.Col(xone.autonomousswitch)
                        ],
                        align="center"
                    )
                ]
            ),
            dbc.Collapse(
                [
                    dbc.CardBody(
                        [
                            html.Div(
                                gvars.childcomponentsbyxoneid[xone.id],
                                id=dict(object="xone", component="child-container", id=xone.id, xoneid=xone.id)
                            )
                        ] + [xone.addchildbutton, xone.deletexonebutton],
                        className='mx-3 mb-3',
                    )
                ],
                id=dict(object="xone", component="collapse", id=xone.id),
                is_open=False,
            ),
        ])

    xonecomponent = html.Div(
        [xone.card, xone.interval, xone.store],
        id=dict(object="xone", component="component", id=xone.id)
    )

    return xonecomponent
