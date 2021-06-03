import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from src.app import app
from src.models import *
import pandas as pd
import dash_table

xoneattrs = ['symbol', 'entry', 'stoploss', 'target', 'status']
childattrs = ['symbol', 'type', 'size', 'status']

db = Db()
session = db.scoped_session()

allchildren = session.query(Child)

allxones = session.query(Xone)

xonedf = pd.DataFrame([{attr: xone.__getattribute__(attr) for attr in xoneattrs} for xone in allxones.all()])
childf = pd.DataFrame([{attr: child.__getattribute__(attr) for attr in childattrs} for child in allchildren.all()])

xones = html.Div([
    dash_table.DataTable(
        id='xones',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in xoneattrs
        ],
        data=xonedf.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=10,
    )],
    style={"padding-bottom": "50px"},
    className="m-3"
)


@app.callback(
    Output('xones', 'style_data_conditional'),
    Input('xones', 'selected_columns')
)
def update_styles(selected_columns):
    return [{
        'if': {'column_id': i},
        'background_color': '#D2F3FF'
    } for i in selected_columns]


children = html.Div([
    dash_table.DataTable(
        id='children',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in childattrs
        ],
        data=childf.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=10,
    )],
    className="m-3"
)


interval = dcc.Interval(
    id='myinterval',
    interval=1000
)

@app.callback(
    Output('children', 'style_data_conditional'),
    Input('children', 'selected_columns')
)
def update_styles(selected_columns):
    return [{
        'if': {'column_id': i},
        'background_color': '#D2F3FF'
    } for i in selected_columns]


@app.callback(
    Output('children', "data"),
    Output('xones', "data"),
    Input('myinterval', "n-intervals")
)
def update_children(n):
    global childf, xonedf
    s = db.scoped_session()
    allchildren = s.query(Child).all()
    childf = pd.DataFrame(
        [{attr: child.__getattribute__(attr) for attr in childattrs} for child in allchildren]).to_dict(
        orient='records')
    allxones = s.query(Xone).all()
    xonedf = pd.DataFrame(
        [{attr: xone.__getattribute__(attr) for attr in xoneattrs} for xone in allxones]).to_dict(orient='records')
    s.commit()
    return childf, xonedf
