from src.myapp import *
from src.accordiontest import createxonecomponents
import src.globalvars as gvars


###########################################
#              Callbacks                  #
###########################################


###################
# Xone Call Backs #
###################


app.clientside_callback(
    """
    function(clicks, state) {
        if (clicks > 0) {
            return ! state
        }
        else {
            return state
        }
    }
    """,
    Output(dict(object="xone", component="collapse", id=MATCH), "is_open"),
    Input(dict(object="xone", component="symbol-button", id=MATCH), "n_clicks"),
    State(dict(object="xone", component="collapse", id=MATCH), "is_open"),
)
# def togglecollapse(clicks, state):
#     if clicks:
#         return not state
#     return state


@app.callback(
    [Output(dict(object="xone", component=f"{attr}-div", id=MATCH), "children") for attr in
     ["status", "lastprice", "pnl"]],
    Input(dict(object="xone", component="interval", id=MATCH), "n_intervals"),
    State(dict(object="xone", component="status-div", id=MATCH), "children"),
    prevent_initial_call=True
)
def updatexoneoninterval(interval, status):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    session = db.scoped_session()
    xone = session.query(Xone).get(id)
    new_status = xone.status.capitalize()
    if new_status == status:
        new_status = dash.no_update
    lastprice = xone.lastprice
    pnl = xone.pnl
    session.close()
    return new_status, lastprice, pnl


@app.callback(
    [Output(dict(object="xone", component=f"{attr}-div", id=MATCH), "style") for attr in
     ["entry", "stoploss", "target"]],
    [Output(dict(object="xone", component="force-button", id=MATCH), attr) for attr in ["style", "disabled"]],
    Output(dict(object="xone", component="force-badge", id=MATCH), "children"),
    Input(dict(object="xone", component="status-div", id=MATCH), "children"),
    Input(dict(object="xone", component="force-button", id=MATCH), "n_clicks"),
    State(dict(object="xone", component="force-badge", id=MATCH), "children")
)
def forceclick(status, n_clicks, count):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update] * 6

    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    component = propdict['component']

    entrystyle = dash.no_update
    stoplossstyle = dash.no_update
    targetstyle = dash.no_update
    forcestyle = dash.no_update
    forcedisabled = dash.no_update
    badgechildren = dash.no_update

    status = status.upper()

    if "status" in component:

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
            xone = session.query(Xone).get(id)
            if status in XoneStatus.PENDING:
                xone.forced_entry = True
            elif status in XoneStatus.OPEN:
                xone.forced_exit = True
            session.commit()
            session.close()

    return entrystyle, stoplossstyle, targetstyle, forcestyle, forcedisabled, badgechildren


@app.callback(
    Output(dict(object="xone", component="autonomous-switch", id=MATCH), "label"),
    Input(dict(object="xone", component="autonomous-switch", id=MATCH), "on"),
    prevent_initial_call=True
)
def toggleautonomous(auto):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    session = db.scoped_session()
    xone = session.query(Xone).get(id)
    xone.autonomous = auto
    session.commit()
    session.close()
    return "Autonomous"


@app.callback(
    Output(dict(object="xone", component="entry-div", id=MATCH), "children"),
    Output(dict(object="xone", component="entry-popover", id=MATCH), "is_open"),
    Input(dict(object="xone", component="entry-modify-button", id=MATCH), "n_clicks"),
    State(dict(object="xone", component="entry-modify-input", id=MATCH), "value"),
    prevent_initial_call=True
)
def modifyentry(n_clicks, value):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    session = db.scoped_session()
    xone = session.query(Xone).get(id)
    xone.entry = value
    session.commit()
    session.close()
    return value, False


@app.callback(
    Output(dict(object="xone", component="stoploss-div", id=MATCH), "children"),
    Output(dict(object="xone", component="stoploss-popover", id=MATCH), "is_open"),
    Input(dict(object="xone", component="stoploss-modify-button", id=MATCH), "n_clicks"),
    State(dict(object="xone", component="stoploss-modify-input", id=MATCH), "value"),
    prevent_initial_call=True
)
def modifystoploss(n_clicks, value):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    session = db.scoped_session()
    xone = session.query(Xone).get(id)
    xone.stoploss = value
    session.commit()
    session.close()
    return value, False


@app.callback(
    Output(dict(object="xone", component="target-div", id=MATCH), "children"),
    Output(dict(object="xone", component="target-popover", id=MATCH), "is_open"),
    Input(dict(object="xone", component="target-modify-button", id=MATCH), "n_clicks"),
    State(dict(object="xone", component="target-modify-input", id=MATCH), "value"),
    prevent_initial_call=True
)
def modifytarget(n_clicks, value):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    session = db.scoped_session()
    xone = session.query(Xone).get(id)
    xone.target = value
    session.commit()
    session.close()
    return value, False


@app.callback(
    Output("createxone-modal", "is_open"),
    Input("createxone-button", "n_clicks"),
    State("createxone-modal", "is_open"),
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open


@app.callback(
    Output("target-input", "value"),
    Output("createxone-form-submit-button", "color"),
    Output("stoploss-formtext", "children"),
    Input("entry-input", "value"),
    Input("stoploss-input", "value"),
    prevent_initial_call=True
)
def warning1(entry, stoploss):
    if entry and stoploss:
        risk = abs(entry - stoploss)
        if entry > stoploss:
            return entry + risk, "success", ""
        elif entry < stoploss:
            return entry - risk, "danger", ""
        else:
            return None, "light", "Stoploss can't be equal to Entry"
    return None, "light", ""


@app.callback(
    Output("target-formtext", "children"),
    Input("target-input", "value"),
    State("entry-input", "value"),
    State("stoploss-input", "value"),
    prevent_initial_call=True
)
def warning2(target, entry, stoploss):
    if not (entry and stoploss and target):
        return ""
    if entry > stoploss and target < entry:
        return "Target must be greater than Entry"
    elif entry < stoploss and target > entry:
        return "Target must be less than Entry"
    return ""


@app.callback(
    Output("createxone-ticker-dropdown", "value"),
    [Output(f"{each}-input", "value") for each in ["entry", "stoploss"]],
    [Output("createxone-form-alert", f"{each}") for each in ["is_open", "children", "color"]],
    Output("xone-container", "children"),
    Input("createxone-form-submit-button", "n_clicks"),
    Input(dict(object="xone", component="delete-button", id=ALL), "n_clicks"),
    State("createxone-ticker-dropdown", "value"),
    [State(f"{each}-input", "value") for each in ["entry", "stoploss", "target"]],
    State("createxone-autonomous-switch", "on"), prevent_initial_call=True
)
def adddeletexone(submit, deletes, ticker, entry, stoploss, target, autonomous):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.exceptions.PreventUpdate
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    if propstr == "createxone-form-submit-button":
        if not (ticker and entry and stoploss and target):
            return dash.no_update, dash.no_update, dash.no_update, True, "All fields required", "danger", dash.no_update
        xonedict = dict(
            symbol=ticker,
            entry=entry,
            stoploss=stoploss,
            target=target,
            autonomous=autonomous)
        response = XoneRequests.create(**xonedict)
        updatedxonecomponents = dash.no_update
        color = "danger"
        if "success" in response.lower():
            color = "success"
            newxoneid = int(response.split(" ")[-1])
            session = db.scoped_session()
            newxone = session.query(Xone).get(newxoneid)
            newcomponent = createxonecomponents(newxone)
            gvars.xonecomponents.insert(0, newcomponent)
            updatedxonecomponents = gvars.xonecomponents
        return None, None, None, True, response, color, updatedxonecomponents

    propdict = eval(propstr)
    id = propdict['id']
    todelete = list(filter(lambda x: x.id['id'] == id, gvars.xonecomponents))[0]
    gvars.xonecomponents.remove(todelete)
    gvars.childcomponentsbyxoneid.pop(id)
    return [dash.no_update] * 6 + [gvars.xonecomponents]



###################
# Child Call Backs#
###################


@app.callback(
    [Output(dict(object="child", component=f"{attr}-div", id=MATCH), "children") for attr in
     ["status", "lastprice", "pnl"]],
    Input(dict(object="child", component="interval", id=MATCH), "n_intervals"),
    State(dict(object="child", component="status-div", id=MATCH), "children"),
    prevent_initial_call=True
)
def updatechildoninterval(interval, status):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    session = db.scoped_session()
    child = session.query(Child).get(id)
    new_status = child.status.capitalize()
    if new_status == status:
        new_status = dash.no_update
    lastprice = child.lastprice
    pnl = child.pnl
    session.close()
    return new_status, lastprice, pnl


@app.callback(
    Output(dict(object="child", component="size-div", id=MATCH), "children"),
    Output(dict(object="child", component="size-popover", id=MATCH), "is_open"),
    Input(dict(object="child", component="size-modify-button", id=MATCH), "n_clicks"),
    State(dict(object="child", component="size-modify-input", id=MATCH), "value"),
    prevent_initial_call=True
)
def modifysize(n_clicks, value):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    session = db.scoped_session()
    child = session.query(Child).get(id)
    child.size = value
    session.commit()
    session.close()
    return value, False


@app.callback(
    Output(dict(object="xone", component="child-container", id=ALL, xoneid=MATCH), "children"),
    Input(dict(object="child", component="delete-button", id=ALL, xoneid=MATCH), "n_clicks"),
    prevent_initial_call=True
)
def adddeletechild(n_clicks):
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    id = propdict['id']
    xoneid = propdict['xoneid']
    todelete = list(filter(lambda x: x.id['id'] == id, gvars.childcomponentsbyxoneid[xoneid]))[0]
    gvars.childcomponentsbyxoneid[xoneid].remove(todelete)
    return [gvars.childcomponentsbyxoneid[xoneid]]


@app.callback(
    Output("addchild-modal", "is_open"),
    Output(dict(object="addchild-form", component="submit-button", xoneid=ALL), "id"),
    Output("addchild-ticker-dropdown", "options"),
    Output("addchild-ticker-dropdown", "value"),
    [Output("size-input", each) for each in ["min", "step", "value"]],
    Output("childtype-radioitems", "value"),
    Input(dict(object="xone", component="addchild-button", id=ALL), "n_clicks"),
    State(dict(object="xone", component="store", id=ALL), "data"),
    State("addchild-modal", "is_open"),
    prevent_initial_call=True
)
def togglemodal(n1, _, is_open):
    if not any(n1):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    # if not propstr:
    #     raise dash.exceptions.PreventUpdate
    propdict = eval(propstr)
    id = propdict['id']
    xstores = ctx.states_list[0]
    underlying = list(filter(lambda x: x['id']['id'] == id, xstores))[0]['value']
    cds = gvars.contracts.query(f"underlying=='{underlying}'")
    tickeroptions = [dict(label=tk, value=tk) for tk in cds["symbol"].to_list()]
    lotsize = cds["lotsize"].values[-1]
    newid = [dict(object="addchild-form", component="submit-button", xoneid=id)]
    return not is_open, newid, tickeroptions, None, lotsize, lotsize, lotsize, "Auto"


@app.callback(
    Output("childtype-radioitems", "labelClassName"),
    Output(dict(object="addchild-form", component="submit-button", xoneid=ALL), "color"),
    Input("childtype-radioitems", "value"),
)
def submitcolor(type):
    if type == "Auto":
        return "btn btn-primary", ["primary"]
    if type == "Buy":
        return "btn btn-success", ["success"]
    if type == "Sell":
        return "btn btn-danger", ["danger"]
    return dash.no_update
