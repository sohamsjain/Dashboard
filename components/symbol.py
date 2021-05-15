import dash_core_components as dcc
from contracts.nifty50 import *


dcc.Dropdown(
        id='symbol',
        options=[
            {'label': 'New York City', 'value': 'NYC'},
            {'label': 'Montreal', 'value': 'MTL'},
            {'label': 'San Francisco', 'value': 'SF'}
        ],
        value='Default',
        placeholder='Default'
    )