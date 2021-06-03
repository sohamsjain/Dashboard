import pandas as pd
from sqlalchemy import create_engine
import backtrader as bt
from src.models import *


conn = create_engine(f'sqlite:///contracts.db', echo=False)
store = bt.stores.IBStore(host="52.70.61.124", port=7497)
store.start()

lotsize = pd.read_csv("https://archives.nseindia.com/content/fo/fo_mktlots.csv")

lotsize.columns = [c.strip() for c in lotsize.columns]

for lc in lotsize.columns:
    lotsize[lc] = lotsize[lc].apply(str.strip)


def get_lotsize(contract_dict):
    symbol = contract_dict['underlying']
    expiry: datetime = contract_dict['expiry']
    if expiry is None:
        return 1
    expiry = pd.to_datetime(expiry)
    strexpiry = expiry.strftime("%B-%y").upper()

    try:
        return int(lotsize.query(f"SYMBOL=='{symbol}'")[str][0])
    except:
        return 1


def create_btsymbol(contract_dict):
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


def get_cds(symbol):
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


supercontract = list()

if __name__ == '__main__':

    old_df = pd.read_sql_table("Contracts", conn)
    all_tickers = old_df[(old_df.sectype == 'IND') | (old_df.sectype == 'STK')].underlying

    for ticker in all_tickers:
        supercontract.extend(get_cds(ticker))

    df = pd.DataFrame(supercontract)
    df["btsymbol"] = df.apply(create_btsymbol, axis=1)
    df.expiry = pd.to_datetime(df.expiry)
    df.to_sql('Contracts', conn, if_exists="replace", index=False)