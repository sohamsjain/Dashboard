from src.myapp import *
from src.models import Xone, Child, relationship
from src.styles import *
from src.util import XoneStatus, XoneType, ChildType
from src.createxoneform import createxonemodal


class DashXone(Xone):
    dashchildren = relationship("DashChild", order_by="DashChild.id", back_populates='dashxone',
                                cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(DashXone, self).__init__(**kwargs)

    def start(self, **kwargs):
        self.started = True
        self.isbullish = True if self.type == XoneType.BULLISH else False

        symbolstyle = {
            'background-color': 'green' if self.isbullish else 'red',
            'color': '#ffffff',
            'border': '1px black solid',
            'font-size': '16px'
        }

        self.symbolbutton = dbc.Button(
            self.symbol,
            id=f"xone-{self.id}-symbol-button",
            style=symbolstyle,
            block=True,
        )

        self.entrydiv = html.Div(
            self.entry,
            id=f"xone-{self.id}-entry-div",
            className=m3,
            style=Styles.Entry[self.status],
        )

        self.entry_popover_children = [
            dbc.PopoverHeader("Modify Entry", style={'font-size': '16px'}),
            dbc.PopoverBody(
                [
                    dcc.Input(
                        id=f"xone-{self.id}-entry-modify-input",
                        className=my2,
                        type="number",
                        value=self.entry
                    ),
                    dbc.Button("Modify", color="primary", block=True, id=f"xone-{self.id}-entry-modify-button")
                ],
                style={'font-size': '12px'}),
        ]

        self.entry_popover = dbc.Popover(
            self.entry_popover_children,
            id=f"xone-{self.id}-entry-popover",
            target=f"xone-{self.id}-entry-div",
            trigger="legacy",
            placement="bottom"
        )

        self.stoplossdiv = html.Div(
            self.stoploss,
            id=f"xone-{self.id}-stoploss-div",
            className=m3,
            style=Styles.Stoploss[self.status])

        self.stoploss_popover_children = [
            dbc.PopoverHeader("Modify Stoploss", style={'font-size': '16px'}),
            dbc.PopoverBody(
                [
                    dcc.Input(
                        id=f"xone-{self.id}-stoploss-modify-input",
                        className=my2,
                        type="number",
                        value=self.stoploss
                    ),
                    dbc.Button("Modify", color="primary", block=True, id=f"xone-{self.id}-stoploss-modify-button")
                ],
                style={'font-size': '12px'}),
        ]

        self.stoploss_popover = dbc.Popover(
            self.stoploss_popover_children,
            id=f"xone-{self.id}-stoploss-popover",
            target=f"xone-{self.id}-stoploss-div",
            trigger="legacy",
            placement="bottom"
        )

        self.targetdiv = html.Div(
            self.target,
            id=f"xone-{self.id}-target-div",
            className=m3,
            style=Styles.Target[self.status])

        self.target_popover_children = [
            dbc.PopoverHeader("Modify Target", style={'font-size': '16px'}),
            dbc.PopoverBody(
                [
                    dcc.Input(
                        id=f"xone-{self.id}-target-modify-input",
                        className=my2,
                        type="number",
                        value=self.target
                    ),
                    dbc.Button("Modify", color="primary", block=True, id=f"xone-{self.id}-target-modify-button")
                ],
                style={'font-size': '12px'}),
        ]

        self.target_popover = dbc.Popover(
            self.target_popover_children,
            id=f"xone-{self.id}-target-popover",
            target=f"xone-{self.id}-target-div",
            trigger="legacy",
            placement="bottom"
        )

        self.statusdiv = html.Div(
            self.status.capitalize(),
            id=f"xone-{self.id}-status-div",
            className=m3,
            style=StyleDefault[self.status])

        self.lastpricediv = html.Div(self.lastprice, id=f"xone-{self.id}-lastprice-div", className=m3,
                                     style=StyleDefault[self.status])

        self.pnldiv = html.Div(self.pnl, id=f"xone-{self.id}-pnl-div", className=m3, style=StyleDefault[self.status])

        forcedisabled, forcecount = True, 0
        if self.status in XoneStatus.PENDING:
            if not self.forced_entry:
                forcedisabled, forcecount = False, 3
        elif self.status in XoneStatus.OPEN:
            if not self.forced_exit:
                forcedisabled, forcecount = False, 3

        self.forcebutton = dbc.Button(
            [
                "Force",
                dbc.Badge(forcecount, id=f"xone-{self.id}-force-badge")
            ],

            id=f"xone-{self.id}-force-button",
            style=StyleForce[self.status],
            className=m3,
            block=True,
            size="sm",
            disabled=forcedisabled
        )

        self.autonomousswitch = BooleanSwitch(
            id=f"xone-{self.id}-autonomous-switch",
            on=self.autonomous,
            color="green",
            label="Autonomous",
            labelPosition="top"
        )

        self.addchildbutton = dbc.Button(
            "Add Child",
            id=f"xone-{self.id}-addchild-button",
            color="primary",
            className=m3
        )

        self.deletexonebutton = dbc.Button(
            "Delete Xone",
            id=f"xone-{self.id}-deletexone-button",
            color="danger",
            className=m3
        )

        self.interval = dcc.Interval(
            id=f"xone-{self.id}-interval",
            interval=1000 * 3,
            n_intervals=0,
        )

    def view(self, addcallbacks):
        try:
            started = self.started
        except AttributeError:
            self.start()

        if addcallbacks:
            self.callbacks()

        card = dbc.Card(
            [
                dbc.CardHeader(
                    [
                        dbc.Row(
                            [
                                dbc.Col(self.symbolbutton),
                                dbc.Col([self.entrydiv, self.entry_popover]),
                                dbc.Col([self.stoplossdiv, self.stoploss_popover]),
                                dbc.Col([self.targetdiv, self.target_popover]),
                                dbc.Col(self.statusdiv),
                                dbc.Col(self.lastpricediv),
                                dbc.Col(self.pnldiv),
                                dbc.Col(self.forcebutton),
                                dbc.Col(self.autonomousswitch)
                            ],
                            align="center"
                        )
                    ]
                ),
                dbc.Collapse(
                    [
                        dbc.CardBody(
                            [
                                child.view(addcallbacks) for child in self.dashchildren
                            ] + [self.addchildbutton, self.deletexonebutton],
                            className='mx-3 mb-3',
                        )
                    ],
                    id=f"xone-{self.id}-collapse",
                    is_open=False,
                ),
            ])

        xone = html.Div(
            [card, self.interval]
        )

        return xone

    def callbacks(self):

        @app.callback(
            Output(f"xone-{self.id}-collapse", "is_open"),
            Input(f"xone-{self.id}-symbol-button", "n_clicks"),
            State(f"xone-{self.id}-collapse", "is_open"),
        )
        def togglecollapse(clicks, state):
            if clicks:
                return not state
            return state

        @app.callback(
            [Output(f"xone-{self.id}-{attr}-div", "children") for attr in ["status", "lastprice", "pnl"]],
            Input(f"xone-{self.id}-interval", "n_intervals"),
            State(f"xone-{self.id}-status-div", "children"),
            prevent_initial_call=True
        )
        def updateoninterval(interval, status):
            session = db.scoped_session()
            session.add(self)
            session.commit()
            new_status = self.status.capitalize()
            if new_status == status:
                new_status = dash.no_update
            lastprice = self.lastprice
            pnl = self.pnl
            session.close()
            return new_status, lastprice, pnl

        @app.callback(
            [Output(f"xone-{self.id}-{attr}-div", "style") for attr in ["entry", "stoploss", "target"]],
            [Output(f"xone-{self.id}-force-button", attr) for attr in ["style", "disabled"]],
            Output(f"xone-{self.id}-force-badge", "children"),
            Input(f"xone-{self.id}-status-div", "children"),
            Input(f"xone-{self.id}-force-button", "n_clicks"),
            State(f"xone-{self.id}-force-badge", "children")
        )
        def forceclick(status, n_clicks, count):
            ctx = dash.callback_context
            if not ctx.triggered:
                return [dash.no_update] * 6

            prop = ctx.triggered[0]["prop_id"].split(".")[0]
            id = int(prop.split("-")[1])

            entrystyle = dash.no_update
            stoplossstyle = dash.no_update
            targetstyle = dash.no_update
            forcestyle = dash.no_update
            forcedisabled = dash.no_update
            badgechildren = dash.no_update

            status = status.upper()

            if "status" in prop:

                entrystyle = StyleEntry[status]
                stoplossstyle = StyleStoploss[status]
                targetstyle = StyleTarget[status]

                if status == XoneStatus.ENTRY:
                    forcestyle = StyleForce[status]
                    forcedisabled = False
                    badgechildren = 3

                elif status in XoneStatus.CLOSED:
                    forcestyle = StyleForce[status]
                    forcedisabled = True
                    badgechildren = 0
            else:
                if count > 0:
                    badgechildren = count - 1
                if badgechildren == 0:
                    forcedisabled = True
                    session = db.scoped_session()
                    xone = session.query(DashXone).get(id)
                    if status in XoneStatus.PENDING:
                        xone.forced_entry = True
                    elif status in XoneStatus.OPEN:
                        xone.forced_exit = True
                    session.commit()
                    session.close()

            return entrystyle, stoplossstyle, targetstyle, forcestyle, forcedisabled, badgechildren

        @app.callback(
            Output(f"xone-{self.id}-autonomous-switch", "label"),
            Input(f"xone-{self.id}-autonomous-switch", "on"),
            prevent_initial_call=True
        )
        def toggleautonomous(auto):
            ctx = dash.callback_context
            prop = ctx.triggered[0]["prop_id"].split(".")[0]
            id = int(prop.split("-")[1])
            session = db.scoped_session()
            xone = session.query(DashXone).get(id)
            xone.autonomous = auto
            session.commit()
            session.close()
            return "Autonomous"

        @app.callback(
            Output(f"xone-{self.id}-entry-div", "children"),
            Output(f"xone-{self.id}-entry-popover", "is_open"),
            Input(f"xone-{self.id}-entry-modify-button", "n_clicks"),
            State(f"xone-{self.id}-entry-modify-input", "value"),
            prevent_initial_call=True
        )
        def modifyentry(n_clicks, value):
            ctx = dash.callback_context
            prop = ctx.triggered[0]["prop_id"].split(".")[0]
            id = int(prop.split("-")[1])
            session = db.scoped_session()
            xone = session.query(DashXone).get(id)
            xone.entry = value
            session.commit()
            session.close()
            return value, False

        @app.callback(
            Output(f"xone-{self.id}-stoploss-div", "children"),
            Output(f"xone-{self.id}-stoploss-popover", "is_open"),
            Input(f"xone-{self.id}-stoploss-modify-button", "n_clicks"),
            State(f"xone-{self.id}-stoploss-modify-input", "value"),
            prevent_initial_call=True
        )
        def modifystoploss(n_clicks, value):
            ctx = dash.callback_context
            prop = ctx.triggered[0]["prop_id"].split(".")[0]
            id = int(prop.split("-")[1])
            session = db.scoped_session()
            xone = session.query(DashXone).get(id)
            xone.stoploss = value
            session.commit()
            session.close()
            return value, False

        @app.callback(
            Output(f"xone-{self.id}-target-div", "children"),
            Output(f"xone-{self.id}-target-popover", "is_open"),
            Input(f"xone-{self.id}-target-modify-button", "n_clicks"),
            State(f"xone-{self.id}-target-modify-input", "value"),
            prevent_initial_call=True
        )
        def modifytarget(n_clicks, value):
            ctx = dash.callback_context
            prop = ctx.triggered[0]["prop_id"].split(".")[0]
            id = int(prop.split("-")[1])
            session = db.scoped_session()
            xone = session.query(DashXone).get(id)
            xone.target = value
            session.commit()
            session.close()
            return value, False


class DashChild(Child):
    dashxone = relationship("DashXone", back_populates="dashchildren")

    def __init__(self, **kwargs):
        super(Child, self).__init__(**kwargs)

    def start(self, **kwargs):
        self.started = True
        self.isbuy = True if self.type == ChildType.BUY else False
        symbolstyle = {
            'background-color': 'green' if self.isbuy else 'red',
            'color': '#ffffff',
            'border': '1px black solid',
            'font-size': '16px'
        }

        self.symbolbutton = dbc.Button(
            self.symbol,
            id=f"child-{self.id}-symbol-button",
            style=symbolstyle,
            block=True
        )

        self.statusdiv = html.Div(self.status.capitalize(), id=f"child-{self.id}-status-div", className=m3,
                                  style=StyleDefault[self.status])
        self.sizediv = html.Div(self.size, id=f"child-{self.id}-size-div", className=m3,
                                style=StyleDefault[self.status])

        self.size_popover_children = [
            dbc.PopoverHeader("Modify Size", style={'font-size': '16px'}),
            dbc.PopoverBody(
                [
                    dcc.Input(
                        id=f"child-{self.id}-size-modify-input",
                        className=my2,
                        type="number",
                        value=self.size,
                        step=self.contract.lotsize
                    ),
                    dbc.Button("Modify", color="primary", block=True, id=f"child-{self.id}-size-modify-button")
                ],
                style={'font-size': '12px'}),
        ]

        self.size_popover = dbc.Popover(
            self.size_popover_children,
            id=f"child-{self.id}-size-popover",
            target=f"child-{self.id}-size-div",
            trigger="legacy",
            placement="bottom"
        )

        self.filleddiv = html.Div(self.filled, id=f"child-{self.id}-filled-div", className=m3,
                                  style=StyleDefault[self.status])
        self.ltpdiv = html.Div(self.lastprice, id=f"child-{self.id}-ltp-div", className=m3,
                               style=StyleDefault[self.status])
        self.pnldiv = html.Div(self.pnl, id=f"child-{self.id}-pnl-div", className=m3, style=StyleDefault[self.status])

        deletestyle = {
            'font-size': '16px'
        }
        self.deletebutton = dbc.Button(
            "Delete Child",
            id=f"child-{self.id}-delete-button",
            # style=deletestyle,
            color="danger",
            block=True,
            size="sm",
            disabled=False
        )

    def view(self, addcallbacks):
        try:
            started = self.started
        except AttributeError:
            self.start()

        if addcallbacks:
            self.callbacks()

        return dbc.CardHeader(
            [
                dbc.Row(
                    [
                        dbc.Col(self.symbolbutton),
                        dbc.Col(self.statusdiv),
                        dbc.Col([self.sizediv, self.size_popover]),
                        dbc.Col(self.filleddiv),
                        dbc.Col(self.ltpdiv),
                        dbc.Col(self.pnldiv),
                        dbc.Col(self.deletebutton, width=1, align="center")
                    ],
                    align="center"
                )
            ]
        )

    def callbacks(self):

        @app.callback(
            Output(f"child-{self.id}-size-div", "children"),
            Output(f"child-{self.id}-size-popover", "is_open"),
            Input(f"child-{self.id}-size-modify-button", "n_clicks"),
            State(f"child-{self.id}-size-modify-input", "value"),
            prevent_initial_call=True
        )
        def modifysize(n_clicks, value):
            ctx = dash.callback_context
            prop = ctx.triggered[0]["prop_id"].split(".")[0]
            id = int(prop.split("-")[1])
            session = db.scoped_session()
            child = session.query(DashChild).get(id)
            child.size = value
            session.commit()
            session.close()
            return value, False


navbar = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    dbc.NavbarBrand("Swayam Capital", className=m3, style={"font-size": "20px", "color": "white"})),
                dbc.Col(
                    dbc.Button(
                        "Create Xone", color="primary", n_clicks=0, id="createxone-button"
                    ),
                    width=1
                ),
            ],
            align="center",
            justify="between"
        ),
    ],
    style={"background-color": "black"}
)





def create_accordion():
    global addcallbacks, xones
    session = db.scoped_session()
    xones = session.query(DashXone).all()

    accordion = html.Div(
        [xone.view(addcallbacks) for xone in xones],
        className="accordion m-3"
    )

    session.close()
    addcallbacks = False
    return accordion


def serve_layout():
    return html.Div([navbar, create_accordion(), createxonemodal])


if __name__ == '__main__':
    xones = list()
    addcallbacks = True
    app.layout = serve_layout

    app.run_server(debug=True)
