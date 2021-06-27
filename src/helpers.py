import datetime
import pandas as pd
import backtrader as bt
from src.constants import NSELOTSIZECSV, HOST, PORT
from src.models import Db

store = None


def getlotsizefromnse():
    lotsize = pd.read_csv(NSELOTSIZECSV)

    lotsize.columns = [c.strip() for c in lotsize.columns]

    for lc in lotsize.columns:
        lotsize[lc] = lotsize[lc].apply(str.strip)

    return lotsize


lotsize = getlotsizefromnse()


def getlotsize(contract_dict):
    symbol = contract_dict['underlying']
    expiry: datetime = contract_dict['expiry']
    if type(expiry) == pd._libs.tslibs.nattype.NaTType:
        return 1
    expiry = pd.to_datetime(expiry)
    strexpiry = expiry.strftime("%b-%y").upper()

    try:
        return int(lotsize.query(f"SYMBOL=='{symbol}'")[strexpiry].values[0])
    except:
        return 1


def createbtsymbol(contract_dict):
    sectype = contract_dict['sectype']
    ticker = contract_dict['underlying'][:9]
    exchange = contract_dict['exchange']
    currency = contract_dict['currency']
    expiry = contract_dict['expiry']
    mult = str(contract_dict['multiplier'])
    strike = str(contract_dict['strike'])
    right = contract_dict['right']

    if sectype in ['IND', 'STK']:
        return "_".join([ticker, sectype, exchange])

    elif sectype == 'FUT':
        return "_".join([ticker, sectype, exchange, currency, expiry[:6], mult])

    elif sectype == 'OPT':
        return "_".join([ticker, sectype, exchange, currency, expiry, strike, right, mult])


def getcds(symbol):
    global store
    sym = symbol[:9]
    list_of_contracts = []
    for sectype in ["IND", "STK", "FUT", "OPT"]:
        contract = store.makecontract(symbol=sym, sectype=sectype, exch="NSE", curr="INR")
        cds = store.getContractDetails(contract)
        if cds is None:
            continue
        for con in cds:
            c = con.contractDetails.m_summary
            list_of_contracts.append(
                dict(
                    id=c.m_conId,
                    underlying=symbol,
                    sectype=c.m_secType,
                    exchange=c.m_exchange,
                    currency=c.m_currency,
                    symbol=c.m_localSymbol,
                    strike=c.m_strike,
                    right=c.m_right,
                    expiry=c.m_expiry,
                    multiplier=c.m_multiplier,
                )
            )
    return list_of_contracts


def updatecontracts():
    global store

    db = Db()
    store = bt.stores.IBStore(host=HOST, port=PORT)
    store.start()

    supercontract = list()
    old_df = pd.read_sql_table("contracts", db.engine)
    all_tickers = old_df[(old_df.sectype == 'IND') | (old_df.sectype == 'STK')].underlying

    for ticker in all_tickers.to_list():
        supercontract.extend(getcds(ticker))

    df = pd.DataFrame(supercontract)
    df["btsymbol"] = df.apply(createbtsymbol, axis=1)
    df.expiry = pd.to_datetime(df.expiry)
    df["lotsize"] = df.apply(getlotsize, axis=1)
    df.to_sql('contracts', db.engine, if_exists="replace", index=False)
    store = None
