import pandas as pd
from sqlalchemy import create_engine
import time

import backtrader as bt
from src.tickers.nifty50 import stock_tickers
from src.tickers.indices import indices_tickers

conn = create_engine(f'sqlite:///contracts.db', echo=False)
store = bt.stores.IBStore(host="52.70.61.124", port=7497)
store.start()


def get_cds(symbol):
    sym = symbol[:9]
    list_of_contracts = []
    for sectype in ["IND", "STK", "FUT", "OPT"]:
        contract = store.makecontract(symbol=sym, sectype=sectype, exch="NSE", curr="INR")
        cds = store.getContractDetails(contract)
        if cds == None:
            continue
        for con in cds:
            c = con.contractDetails.m_summary
            list_of_contracts.append(
                dict(
                    id=c.m_conId,
                    symbol=symbol,
                    sectype=c.m_secType,
                    exchange=c.m_exchange,
                    currency=c.m_currency,
                    localSymbol=c.m_localSymbol,
                    strike=c.m_strike,
                    right=c.m_right,
                    expiry=c.m_expiry,
                    multiplier=c.m_multiplier,
                )
            )
    return list_of_contracts

st = time.perf_counter()


supercontract = list()
for ticker in indices_tickers + stock_tickers:
    supercontract.extend(get_cds(ticker))

df = pd.DataFrame(supercontract)
df.to_sql('Contracts', conn, if_exists="replace", index=False)
sp = time.perf_counter()
print(sp-st)
input()