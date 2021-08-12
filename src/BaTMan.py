from datetime import datetime
from queue import Queue
import sys
import schedule
import traceback
import time
from threading import Thread
from typing import List, Dict, Optional, Union, Tuple
import backtrader as bt
from src.mysizer import MySizer
from src.strategy import Grid
from src.constants import HOST, PORT, YESTERDAY
from src.helpers import updatecontracts
from src.models import Db, Child, Xone, Contract, scoped_session, NoResultFound, MultipleResultsFound, or_, \
    StatementError, OperationalError
from src.util import ChildStatus, XoneType, ChildType, XoneStatus


class BaTMan:

    def __init__(self):

        self.db = Db()
        self.session: Optional[scoped_session] = None

        self.cerebro: Optional[bt.Cerebro] = None
        self.store: Optional[bt.stores.IBStore] = None

        self.alldatas: Dict[str, bt.feeds.IBData] = dict()

        self.allxones: List[Xone] = list()
        self.openxones: List[Xone] = list()
        self.allchildren: List[Child] = list()
        self.xonesbybtsymbol: Dict[str, List[Xone]] = dict()

        self.market = False
        self.sessionq: Optional[Queue] = None

        self.schedulerthread = Thread(target=self.scheduler, name="scheduler")
        self.schedulerthread.start()

    def scheduler(self):
        schedule.every().day.at("09:10").do(self.run)
        schedule.every().friday.at("06:15").do(updatecontracts)
        while 1:
            schedule.run_pending()
            time.sleep(1)

    def createxone(self, dictionary):
        session = self.db.scoped_session()

        xonekwargs = {key: val for key, val in dictionary.items() if val != ''}

        for attr in ["symbol", "entry", "stoploss"]:
            if attr not in xonekwargs:
                return f"Missing Xone Attribute: {attr}"

        symbol = xonekwargs['symbol']
        if not isinstance(symbol, str):
            return f"symbol must be a string: {symbol}"
        symbol = symbol.upper()

        try:
            contract = session.query(Contract).filter(Contract.symbol == symbol).one()
        except NoResultFound:
            return f"Invalid Symbol: {symbol}"
        except MultipleResultsFound:
            return f"Multiple Contracts found for Symbol: {symbol}"

        entry = xonekwargs['entry']
        try:
            entry = float(entry)
        except ValueError:
            return f"Entry must be of type (float, int), found {type(entry)} instead"

        stoploss = xonekwargs['stoploss']
        try:
            stoploss = float(stoploss)
        except ValueError:
            return f"Stoploss must be of type (float, int), found {type(stoploss)} instead"

        if entry == stoploss:
            return "Entry cannot be equal to Stoploss"

        target = xonekwargs['target']
        try:
            target = float(target)
        except ValueError:
            return f"Target must be of type (float, int), found {type(target)} instead"

        children = xonekwargs.get('children', [])
        # if not children:
        #     return f"Xone must have a child, none found"

        xone = Xone(
            contract_id=contract.id,
            symbol=symbol,
            sectype=contract.sectype,
            btsymbol=contract.btsymbol,
            expiry=contract.expiry,
            entry=entry,
            stoploss=stoploss,
            target=target,
            type=XoneType.identify(entry, stoploss),
            kid_count=len(children)
        )

        children_objects = list()

        for c in children:
            kidkwargs = {key: val for key, val in c.items() if val != ''}

            if "symbol" not in kidkwargs:
                return f"Missing Child Attribute: symbol"

            kidsymbol = kidkwargs['symbol']
            if not isinstance(kidsymbol, str):
                return f"symbol must be a string: {kidsymbol}"
            kidsymbol = kidsymbol.upper()

            try:
                kidcontract = session.query(Contract).filter(Contract.symbol == kidsymbol).one()
            except NoResultFound:
                return f"Invalid Symbol: {kidsymbol}"
            except MultipleResultsFound:
                return f"Multiple Contracts found for Symbol: {kidsymbol}"

            kidtype = kidkwargs.get("type", None)
            if kidtype is None:
                kidtype = ChildType.BUY if xone.type == XoneType.BULLISH else ChildType.SELL
                kidtype = ChildType.invert(kidtype) if kidcontract.right == "P" else kidtype

            size = kidkwargs.get('size', None)
            if size and not isinstance(size, int):
                return "Size must be of type int"

            child = Child(
                parent_id=xone.id,
                contract_id=contract.id,
                symbol=kidsymbol,
                sectype=kidcontract.sectype,
                btsymbol=kidcontract.btsymbol,
                expiry=kidcontract.expiry,
                type=kidtype,
                size=size
            )

            children_objects.append(child)

        xone.children = children_objects

        session.add(xone)
        session.commit()

        if self.market:

            restart = False
            xone.start()
            xone.data, dorestart = self.getdata(xone.btsymbol)
            restart = dorestart if not restart and dorestart else restart

            for child in xone.children:
                child.start()
                child.data, dorestart = self.getdata(child.btsymbol)
                restart = dorestart if not restart and dorestart else restart

            if restart:
                self.cerebro.runrestart()

            session.expunge(xone)
            self.sessionq.put(xone)

        return "Xone Created Successfully"

    def removexone(self, xone):
        xonesofakind = self.xonesbybtsymbol[xone.btsymbol]
        xonesofakind.remove(xone)
        if not xonesofakind:
            self.xonesbybtsymbol.pop(xone.btsymbol)

        if xone in self.allxones:
            self.allxones.remove(xone)

        for child in xone.children:

            if child in self.allchildren:
                self.allchildren.remove(child)

    # def deletexone(self, xone_id):
    #     session = self.db.scoped_session()
    #     xone = session.query(Xone).get(xone_id)
    #
    #     if xone is None:
    #         return f"Xone with id {xone_id} does not exist"
    #
    #     if xone.status in XoneStatus.OPEN:
    #         return f"Xone with id {xone_id} is in open state. Cannot delete an open xone"
    #
    #     if self.market:
    #         self.removexone(xone)
    #
    #     session.delete()



    def getdata(self, btsymbol) -> Union[bt.feeds.IBData, Tuple[bt.feeds.IBData, bool]]:

        data = None
        dorestart = False

        if btsymbol in self.alldatas:
            data = self.alldatas[btsymbol]

        if data is None:
            data = self.store.getdata(dataname=btsymbol, rtbar=True, backfill_start=False)
            self.cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=5)
            # data = self.store.getdata(dataname=btsymbol, historical=True)  # , fromdate=yesterday)
            # self.cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1)
            self.alldatas[btsymbol] = data
            dorestart = True

        if not self.market:
            return data

        if not dorestart:
            return data, dorestart

        data.reset()

        if self.cerebro._exactbars < 1:
            data.extend(size=self.cerebro.params.lookahead)

        data._start()

        if self.cerebro._dopreload:
            data.preload()

        return data, dorestart

    def addxone(self, xone):
        if xone.btsymbol not in self.xonesbybtsymbol:
            self.xonesbybtsymbol[xone.btsymbol] = list()

        self.xonesbybtsymbol[xone.btsymbol].append(xone)

        if xone._sa_instance_state.session is None:
            self.session.add(xone)

        if xone not in self.allxones:
            self.allxones.append(xone)

        for child in xone.children:

            if child not in self.allchildren:
                self.allchildren.append(child)

            if child._sa_instance_state.session is None:
                self.session.add(child)

    def run(self):
        try:
            self.alldatas.clear()
            self.allxones.clear()
            self.openxones.clear()
            self.allchildren.clear()
            self.xonesbybtsymbol.clear()

            if datetime.now().date().weekday() not in range(5):
                print("Happy Holiday")
                return

            self.session = self.db.scoped_session()

            self.cerebro = bt.Cerebro()

            self.store = bt.stores.IBStore(host=HOST, port=PORT)
            self.getdata("INFY_STK_NSE")

            self.allchildren = self.session.query(Child).filter(
                or_(Child.status == ChildStatus.CREATED, Child.status == ChildStatus.BOUGHT,
                    Child.status == ChildStatus.SOLD)).all()

            self.allxones = self.session.query(Xone).filter(
                or_(Xone.status == XoneStatus.CREATED, Xone.status == XoneStatus.ENTRYHIT,
                    Xone.status == XoneStatus.ENTRY, Xone.status == XoneStatus.STOPLOSSHIT,
                    Xone.status == XoneStatus.TARGETHIT)).all()

            self.openxones = self.session.query(Xone).filter(Xone.status == XoneStatus.ENTRY,
                                                             Xone.status == XoneStatus.STOPLOSSHIT,
                                                             Xone.status == XoneStatus.TARGETHIT).all()

            for xone in self.allxones:
                xone.start()
                xone.data = self.getdata(xone.btsymbol)

                for child in xone.children:
                    child.start()
                    child.data = self.getdata(child.btsymbol)

                self.addxone(xone)

            self.cerebro.setbroker(self.store.getbroker())

            self.cerebro.addstrategy(Grid, batman=self)

            self.cerebro.addsizer(MySizer)

            self.cerebro.run()

        except StatementError as se:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            self.session.rollback()
            self.run()

        except OperationalError as oe:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            self.session.rollback()
            self.db = Db()
            self.run()

        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)

        if self.store.dontreconnect:
            self.store.dontreconnect = False

        del self.cerebro, self.store
        print("run thread ends: ")


