from src.myapp import *
from src.accordiontest import createxonecomponents, createchildcomponents
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
    [Output(dict(object="xone", component=f"{attr}-div", id=ALL), "children") for attr in
     ["status", "lastprice", "pnl"]],
    [Output(dict(object="child", component=f"{attr}-div", id=ALL), "children") for attr in
     ["status", "lastprice", "pnl"]],
    Input("interval", "n_intervals"),
    State(dict(object="xone", component="status-div", id=ALL), "children"),
    prevent_initial_call=True
)
def updateoninterval(interval, oldstatuses):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    currentstatusbyid = {k["id"]["id"]: k["value"] for k in ctx.states_list[0]}
    try:
        session = db.scoped_session()
        xonestatuses, xonelastprices, xonepnls = list(), list(), list()
        ids = [component["id"]["id"] for component in ctx.outputs_list[0]]
        for id in ids:
            xone = session.query(Xone).get(id)
            new_status = xone.status.capitalize()
            if new_status == currentstatusbyid[id]:
                new_status = dash.no_update
            xonestatuses.append(new_status)
            xonelastprices.append(xone.lastprice)
            xonepnls.append(xone.pnl)
        childstatuses, childlastprices, childpnls = list(), list(), list()
        ids = [component["id"]["id"] for component in ctx.outputs_list[3]]
        for id in ids:
            child = session.query(Child).get(id)
            childstatuses.append(child.status.capitalize())
            childlastprices.append(child.lastprice)
            childpnls.append(child.pnl)
        session.close()
        return xonestatuses, xonelastprices, xonepnls, childstatuses, childlastprices, childpnls
    except AttributeError as ae:
        raise dash.exceptions.PreventUpdate


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
            return round(entry + risk, 2), "success", ""
        elif entry < stoploss:
            return round(entry - risk, 2), "danger", ""
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
    response = XoneRequests.delete(xone_id=id)
    if "success" in response.lower():
        todelete = list(filter(lambda x: x.id['id'] == id, gvars.xonecomponents))[0]
        gvars.xonecomponents.remove(todelete)
        gvars.childcomponentsbyxoneid.pop(id)
        return [dash.no_update] * 6 + [gvars.xonecomponents]
    return [dash.no_update] * 7



###################
# Child Call Backs#
###################


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
    [Output("addchild-form-alert", f"{each}") for each in ["is_open", "children", "color"]],
    Output(dict(object="xone", component="child-container2", id=ALL, xoneid=ALL), "children"),
    Input(dict(object="addchild-form", component="submit-button"), "n_clicks"),
    [State(each, "value") for each in ["addchild-ticker-dropdown", "size-input", "childtype-radioitems"]],
    State("store-xoneid", "data"),
    prevent_initial_call=True
)
def addchild(_, ticker, size, type, xoneid):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    newcomponents = [dash.no_update] * len(ctx.outputs_list[3])
    color = "danger"
    if not(ticker and size):
        return True, "All fields required", color, newcomponents
    childdict = dict(
        xone_id=xoneid,
        symbol=ticker,
        size=size)
    if type != "Auto":
        childdict.update(dict(type=type.upper()))
    response = ChildRequests.create(**childdict)
    if "success" in response.lower():
        newcomponents = [True if component["id"]["id"] == xoneid else dash.no_update for component in
                         ctx.outputs_list[3]]
        index = newcomponents.index(True)
        color = "success"
        newchildid = int(response.split(" ")[-1])
        session = db.scoped_session()
        newchild = session.query(Child).get(newchildid)
        newcomponent = createchildcomponents(newchild)
        gvars.childcomponentsbyxoneid[xoneid].append(newcomponent)
        updatedchildcomponents = html.Div(
            gvars.childcomponentsbyxoneid[xoneid],
            id=dict(object="xone", component="child-container1", id=xoneid, xoneid=xoneid)
        )
        newcomponents[index] = updatedchildcomponents
    return True, response, color, newcomponents


@app.callback(
    Output(dict(object="xone", component="child-container1", id=ALL, xoneid=MATCH), "children"),
    Input(dict(object="child", component="delete-button", id=ALL, xoneid=MATCH), "n_clicks"),
    prevent_initial_call=True
)
def deletechild(_):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    propstr = ctx.triggered[0]["prop_id"].split(".")[0]
    propdict = eval(propstr)
    xoneid = propdict['xoneid']
    id = propdict['id']
    updatedchildcomponents = dash.no_update
    response = ChildRequests.delete(**dict(child_id=id))
    if "success" in response.lower():
        todelete = list(filter(lambda x: x.id['id'] == id, gvars.childcomponentsbyxoneid[xoneid]))[0]
        gvars.childcomponentsbyxoneid[xoneid].remove(todelete)
        updatedchildcomponents = [gvars.childcomponentsbyxoneid[xoneid]]
    return updatedchildcomponents


@app.callback(
    Output("addchild-modal", "is_open"),
    Output("store-xoneid", "data"),
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
    propdict = eval(propstr)
    id = propdict['id']
    xstores = ctx.states_list[0]
    underlying = list(filter(lambda x: x['id']['id'] == id, xstores))[0]['value']
    cds = gvars.contracts.query(f"underlying=='{underlying}'")
    tickeroptions = [dict(label=tk, value=tk) for tk in cds["symbol"].to_list()]
    lotsize = cds["lotsize"].values[-1]
    return not is_open, id, tickeroptions, None, lotsize, lotsize, lotsize, "Auto"


app.clientside_callback(
    """
    function(type){
        if (type == "Auto"){
            return ["btn btn-primary", ["primary"]]
        }
        else if (type == "Buy"){
            return ["btn btn-success", ["success"]]
        }
        else if (type == "Sell"){
            return ["btn btn-danger", ["danger"]]
        }
    }
    """,
    Output("childtype-radioitems", "labelClassName"),
    Output(dict(object="addchild-form", component="submit-button", xoneid=ALL), "color"),
    Input("childtype-radioitems", "value"),
)
