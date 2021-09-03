import pandas as pd

contracts = list()
tickers = list()
xonecomponents = list()
childcomponentsbyxoneid = dict()

def refreshcontracts():
    global contracts, tickers
    contracts = pd.read_sql_table("contracts", db.engine)
    tickers = contracts.query("sectype!='OPT'")["symbol"].to_list()

refreshcontracts()