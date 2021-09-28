from src.myapp import *
from src.accordiontest import createxonecomponents
import src.callbacks
from src.createxoneform import createxonemodal
from src.addchildform import addchildmodal
import src.globalvars as gvars


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

interval = dcc.Interval(
        id="interval",
        interval=1000 * 3,
        n_intervals=0,
    )


def serve_layout():
    global xonecomponents
    session = db.scoped_session()
    xones = session.query(Xone).all()
    gvars.xonecomponents = [createxonecomponents(xone) for xone in xones]
    accordion = html.Div(
        gvars.xonecomponents,
        className="accordion m-3",
        id="xone-container"
    )
    session.close()
    return html.Div([navbar, accordion, createxonemodal, addchildmodal, interval])


if __name__ == '__main__':

    app.layout = serve_layout

    app.run_server(host="0.0.0.0", port=9999)