import time
from typing import Optional
import datetime
import pandas as pd
import backtrader as bt
from src.constants import NSELOTSIZECSV, HOST, PORT
from src.models import *


store = None
db = None
lotsize: Optional[pd.DataFrame] = None


def getlotsizefromnse():
    global lotsize
    lotsize = pd.read_csv(NSELOTSIZECSV)

    lotsize.columns = [c.strip() for c in lotsize.columns]

    for lc in lotsize.columns:
        lotsize[lc] = lotsize[lc].apply(str.strip)

    return lotsize


getlotsizefromnse()


def getlotsize(contract_dict):
    symbol = contract_dict['underlying']
    expiry = contract_dict['expiry']
    if expiry is None:
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
    if "&" in ticker:
        ticker = ticker.replace("&", "")
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


def addcontract(symbol):
    global store, db
    added = 0
    existed = 0
    sym = symbol[:9]
    if "&" in sym:
        sym = sym.replace("&", "")
    for sectype in ["OPT", "IND", "STK", "FUT"]:
        contract = store.makecontract(symbol=sym, sectype=sectype, exch="NSE", curr="INR")
        start = time.perf_counter()
        cds = store.getContractDetails(contract)
        stop = time.perf_counter()
        print(f"{symbol} {sectype} time: {stop-start}s")
        if cds is None:
            continue
        cds = [con.contractDetails.m_summary for con in cds]
        session = db.scoped_session()
        existingcontracts = session.query(Contract).filter(and_(Contract.underlying == symbol, Contract.sectype == sectype)).all()
        existingsymbols = [con.symbol for con in existingcontracts] if existingcontracts else []
        if existingsymbols:
            l1 = len(cds)
            cds = [con for con in cds if con.m_localSymbol not in existingsymbols]
            l2 = len(cds)
            existed += l1-l2
        newcontracts = []
        for c in cds:
            newcontractdictionary = dict(
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
            newcontractdictionary.update(dict(btsymbol=createbtsymbol(newcontractdictionary),
                                              lotsize=getlotsize(newcontractdictionary)))
            newcontract = Contract(**newcontractdictionary)
            newcontracts.append(newcontract)
        added += len(newcontracts)
        session.add_all(newcontracts)
        session.commit()
        session.close()
    return added, existed


def updatecontracts():
    global store, db
    db = Db()
    print("Deleting unused expired contracts...", end="\t")
    deleted = deleteexpiredcontracts()
    print(f"{deleted} deleted!")
    store = bt.stores.IBStore(host=HOST, port=PORT)
    if store.dontreconnect:
        store.dontreconnect = False
    store.start()
    getlotsizefromnse()
    all_tickers: list = lotsize[(lotsize.SYMBOL != 'Symbol')].SYMBOL.to_list()
    if "NIFTY" in all_tickers:
        all_tickers[all_tickers.index("NIFTY")] = "NIFTY50"
    print("Updating Contracts...")
    for ticker in all_tickers[:]:
        print(f"Updating {ticker}...")
        added, existed = addcontract(ticker)
        print(f"Added: {added}, Existed:{existed}")

    store.stop()
    store = None
    db.engine.dispose()
    db = None
    print("update successful...")


def deleteexpiredcontracts():
    global db
    deleted = 0
    session = db.scoped_session()
    allcontracts = session.query(Contract).filter(or_(Contract.sectype == SecType.FUT,
                                                      Contract.sectype == SecType.OPT)).all()
    for contract in allcontracts:
        if contract.expiry.date() < datetime.now().date():
            try:
                session.delete(contract)
                session.commit()
                deleted += 1
            except IntegrityError as ae:
                session.rollback()
    session.close()
    return deleted


if __name__ == '__main__':
    updatecontracts()