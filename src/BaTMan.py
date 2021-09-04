from datetime import datetime
from queue import Queue
import sys
import schedule
import traceback
import time
from threading import Thread
from typing import List, Dict, Optional
import backtrader as bt
from src.mysizer import MySizer
from src.strategy import Grid
from src.constants import HOST, PORT, YESTERDAY, SESSIONSTART, SESSIONEND
from src.helpers import updatecontracts
from src.models import Db, Child, Xone, Contract, scoped_session, NoResultFound, MultipleResultsFound, or_, \
    StatementError, OperationalError
from src.util import ChildStatus, XoneType, ChildType, XoneStatus, RequestType, ResponseType


class BaTMan:

    def __init__(self):

        self.db = Db()
        self.session: Optional[scoped_session] = None

        self.cerebro: Optional[bt.Cerebro] = None
        self.store: Optional[bt.stores.IBStore] = None

        self.alldatas: Dict[str, bt.feeds.IBData] = dict()

        self.allxones: List[Xone] = list()
        self.allchildren: List[Child] = list()
        self.openxones: List[Xone] = list()

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

    def addxone(self, xone):
        if xone not in self.allxones:
            self.allxones.append(xone)

        for child in xone.children:
            self.addchild(child)

    def removexone(self, xone):
        if xone in self.allxones:
            self.allxones.remove(xone)

        for child in xone.children:
            self.removechild(child)

    def addchild(self, child):
        if child not in self.allchildren:
            self.allchildren.append(child)

    def removechild(self, child):
        if child in self.allchildren:
            self.allchildren.remove(child)

    def createxone(self, dictionary):
        session = self.db.scoped_session()

        xonekwargs = {key: val for key, val in dictionary.items() if val}

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
            autonomous=xonekwargs.get('autonomous', True),
            kid_count=len(children) if children is not None else 0
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
                contract_id=kidcontract.id,
                symbol=kidsymbol,
                sectype=kidcontract.sectype,
                btsymbol=kidcontract.btsymbol,
                expiry=kidcontract.expiry,
                type=kidtype,
                size=size
            )

            children_objects.append(child)

        xone.children = children_objects

        if self.market:

            xone.start()
            xone.data = self.getdata(xone.btsymbol)

            for child in xone.children:
                child.start()
                child.data = self.getdata(child.btsymbol)

            q = Queue()
            message = dict(head=RequestType.ADDXONE, body=xone, responseq=q)
            self.sessionq.put(message)

            response = q.get()
            if response == ResponseType.ADDXONESUCCESS:
                return "Xone Created Successfully"
            elif response == ResponseType.ADDXONEFAILURE:
                return "Xone Could not be created"

        else:
            session.add(xone)
            session.commit()
            return f"Xone Created Successfully {xone.id}"

    def updatexone(self, dictionary):
        updatekwargs = {key: val for key, val in dictionary.items() if val != ''}

        xone_id = updatekwargs.get('xone_id', None)
        if xone_id is None:
            return f"Missing Xone Attribute: xone_id"
        if not isinstance(xone_id, int):
            return f"xone_id must be a int: {xone_id}"

        session = self.db.scoped_session()
        xone = session.query(Xone).get(xone_id)

        entry = updatekwargs.get('entry', None)
        if entry is not None:

            if not isinstance(entry, float):
                return f"entry must be a float: {entry}"

            if xone.status not in XoneStatus.PENDING:
                return f"can't modify entry in XoneStatus: {xone.status}"

            xone.entry = entry
            if xone.status == XoneStatus.ENTRYHIT:
                if xone.type == XoneType.BULLISH:
                    if entry < xone.lastprice:
                        xone.status = XoneStatus.CREATED
                else:
                    if entry > xone.lastprice:
                        xone.status = XoneStatus.CREATED

        stoploss = updatekwargs.get('stoploss', None)
        if stoploss is not None:

            if not isinstance(stoploss, float):
                return f"stoploss must be a float: {stoploss}"

            if xone.status in XoneStatus.CLOSED:
                return f"can't modify stoploss in XoneStatus: {xone.status}"

            xone.stoploss = stoploss
            if xone.status == XoneStatus.STOPLOSSHIT:
                if xone.type == XoneType.BULLISH:
                    if stoploss < xone.lastprice:
                        xone.status = XoneStatus.ENTRY
                else:
                    if stoploss > xone.lastprice:
                        xone.status = XoneStatus.ENTRY

        target = updatekwargs.get('target', None)
        if target is not None:

            if not isinstance(target, float):
                return f"target must be a float: {target}"

            if xone.status in XoneStatus.CLOSED:
                return f"can't modify target in XoneStatus: {xone.status}"

            xone.target = target
            if xone.status == XoneStatus.TARGETHIT:
                if xone.type == XoneType.BULLISH:
                    if target > xone.lastprice:
                        xone.status = XoneStatus.ENTRY
                else:
                    if target < xone.lastprice:
                        xone.status = XoneStatus.ENTRY

        autonomous = updatekwargs.get('autonomous', None)
        if autonomous is not None:
            if not isinstance(autonomous, bool):
                return f"autonomous must be a bool: {autonomous}"

            xone.autonomous = autonomous

        forced_entry = updatekwargs.get('forced_entry', None)
        if forced_entry is not None:
            if not isinstance(forced_entry, bool):
                return f"forced_entry must be a bool: {forced_entry}"

            if xone.status not in XoneStatus.PENDING:
                return f"can't force entry in XoneStatus: {xone.status}"

            xone.forced_entry = forced_entry

        forced_exit = updatekwargs.get('forced_exit', None)
        if forced_exit is not None:
            if not isinstance(forced_exit, bool):
                return f"forced_exit must be a bool: {forced_exit}"

            if xone.status not in XoneStatus.OPEN:
                return f"can't force exit in XoneStatus: {xone.status}"

            xone.forced_exit = forced_exit

        session.commit()
        session.close()
        return "Update Successful"

    def deletexone(self, xone_id):
        session = self.db.scoped_session()
        xone = session.query(Xone).get(xone_id)

        if xone is None:
            return f"Xone with id {xone_id} does not exist"

        if xone.status in XoneStatus.OPEN:
            return f"Xone with id {xone_id} is in open state. Cannot delete an open xone"

        if xone.status in XoneStatus.CLOSED:
            return f"Xone with id {xone_id} is in closed state. Cannot delete a closed xone"

        if self.market:
            q = Queue()
            message = dict(head=RequestType.DELETEXONE, body=xone_id, responseq=q)
            self.sessionq.put(message)

            response = q.get()
            if response == ResponseType.DELETEXONESUCCESS:
                return f"Xone with id {xone_id} deleted successfully"
            elif response == ResponseType.DELETEXONEFAILURE:
                return f"Xone with id {xone_id} could not be deleted"
        else:
            session.delete(xone)
            session.commit()

            return f"Xone with id {xone_id} deleted successfully"

    def createchild(self, dictionary):
        session = self.db.scoped_session()

        kidkwargs = {key: val for key, val in dictionary.items() if val != ''}

        xone_id = kidkwargs.get('xone_id', None)

        if not xone_id:
            return "Missing attribute xone_id"

        xone = session.query(Xone).get(xone_id)

        if xone is None:
            return f"Xone with id {xone_id} does not exist"

        if xone.status in XoneStatus.OPEN:
            return f"Xone with id {xone_id} is in open state. Cannot add a child to an open xone"

        if xone.status in XoneStatus.CLOSED:
            return f"Xone with id {xone_id} is in closed state. Cannot add a child to a closed xone"

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
            contract_id=kidcontract.id,
            symbol=kidsymbol,
            sectype=kidcontract.sectype,
            btsymbol=kidcontract.btsymbol,
            expiry=kidcontract.expiry,
            type=kidtype,
            size=size
        )

        if self.market:

            child.start()
            child.data = self.getdata(child.btsymbol)

            q = Queue()
            body = dict(child=child, xone_id=xone_id)
            message = dict(head=RequestType.ADDCHILD, body=body, responseq=q)
            self.sessionq.put(message)

            response = q.get()
            if response == ResponseType.ADDCHILDSUCCESS:
                return "Child created successfully"
            elif response == ResponseType.ADDCHILDFAILURE:
                return "Child could not be created"

        else:
            xone.children.append(child)
            xone.kid_count += 1
            session.commit()
            return "Child created Successfully"

    def updatechild(self, dictionary):
        updatekwargs = {key: val for key, val in dictionary.items() if val != ''}

        child_id = updatekwargs.get('child_id', None)

        if child_id is None:
            return f"Missing Child Attribute: child_id"

        if not isinstance(child_id, int):
            return f"child_id must be a int: {child_id}"

        session = self.db.scoped_session()
        child = session.query(Child).get(child_id)

        size = updatekwargs.get('size', None)
        if size is not None:

            if not isinstance(size, int):
                return f"size must be a int: {size}"

            if child.status not in ChildStatus.CREATED:
                return f"can't modify size in ChildStatus: {child.status}"

            lotsize = child.contract.lotsize
            if not size % child.contract.lotsize == 0:
                return f"size must be a multiple of lotsize: {lotsize}"

            child.size = size

        session.commit()
        session.close()
        return "Update Successful"

    def deletechild(self, child_id):
        session = self.db.scoped_session()
        child = session.query(Child).get(child_id)

        if child is None:
            return f"Child with id {child_id} does not exist"

        if child.status in ChildStatus.OPEN:
            return f"Child with id {child_id} is in open state. Cannot delete an open child"

        if child.status in ChildStatus.CLOSED:
            return f"Child with id {child_id} is in closed state. Cannot delete a closed child"

        if self.market:
            q = Queue()
            message = dict(head=RequestType.DELETECHILD, body=child_id, responseq=q)
            self.sessionq.put(message)

            response = q.get()
            if response == ResponseType.DELETECHILDSUCCESS:
                return f"Child with id {child_id} deleted successfully"
            elif response == ResponseType.DELETECHILDFAILURE:
                return f"Child with id {child_id} could not be deleted"
        else:
            xone = child.xone
            xone.children.remove(child)
            xone.kid_count -= 1
            session.commit()

            return f"Child with id {child_id} deleted successfully"

    def getdata(self, btsymbol) -> bt.feeds.IBData:

        data = None
        dorestart = False

        if btsymbol in self.alldatas:
            data = self.alldatas[btsymbol]

        if data is None:
            data = self.store.getdata(dataname=btsymbol, rtbar=True, backfill_start=False, sessionstart=SESSIONSTART,
                                      sessionend=SESSIONEND)
            self.cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=5)
            # data = self.store.getdata(dataname=btsymbol, historical=True, fromdate=YESTERDAY)
            # self.cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1)
            self.alldatas[btsymbol] = data
            dorestart = True

        if not self.market:
            return data

        if not dorestart:
            return data

        data.reset()

        if self.cerebro._exactbars < 1:
            data.extend(size=self.cerebro.params.lookahead)

        data._start()

        if self.cerebro._dopreload:
            data.preload()

        self.cerebro.runrestart()

        return data

    def run(self):
        try:
            self.alldatas.clear()
            self.allxones.clear()
            self.allchildren.clear()
            self.openxones.clear()
            self.market = False

            if datetime.now().date().weekday() not in range(5):
                print("Happy Holiday")
                return

            self.session = self.db.scoped_session()

            self.cerebro = bt.Cerebro()

            self.store = bt.stores.IBStore(host=HOST, port=PORT)

            if self.store.dontreconnect:
                self.store.dontreconnect = False

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

        del self.cerebro, self.store
        print("run thread ends: ")
