import sys
import traceback
from threading import Thread
from typing import List, Dict, Optional, Callable, Union, Tuple
from src.mysizer import MySizer
from src.strategy import *

HOST, PORT = "52.70.61.124", 7497


class BaTMan:

    def __init__(self):
        self.db = Db()
        self.session = self.db.session
        self.cerebro: Optional[bt.Cerebro] = None
        self.store: Optional[bt.stores.IBStore] = None
        self.alldatas: Dict[str, bt.feeds.IBData] = dict()
        self.allxones: List[Xone] = list()
        self.openxones: List[Xone] = list()
        self.xonesbybtsymbol: Dict[str, List[Xone]] = dict()
        self.market = False
        self.addxonecb: Optional[Callable] = None
        self.runthread = Thread(target=self.run, name="runthread").start()

    def create(self, dictionary):

        xonekwargs = {key: val for key, val in dictionary.items() if val != ''}

        for attr in ["symbol", "entry", "stoploss"]:
            if attr not in xonekwargs:
                return f"Missing Xone Attribute: {attr}"

        symbol = xonekwargs['symbol']
        if not isinstance(symbol, str):
            return f"symbol must be a string: {symbol}"
        symbol = symbol.upper()

        try:
            contract = self.session.query(Contract).filter(Contract.symbol == symbol).one()
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
        if not children:
            return f"Xone must have a child, none found"

        xone = Xone(
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
                kidcontract = self.session.query(Contract).filter(Contract.symbol == kidsymbol).one()
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
            self.addxonecb(xone)
            self.allxones.append(xone)
            self.add(xone)

        self.session.add(xone)
        self.session.commit()

        return "Xone Created Successfully"

    def remove(self, xone):
        xonesofakind = self.xonesbybtsymbol[xone.btsymbol]
        xonesofakind.remove(xone)
        if not xonesofakind:
            self.xonesbybtsymbol.pop(xone.btsymbol)

    def getdata(self, btsymbol, fromcb=False) -> Union[bt.feeds.IBData, Tuple[bt.feeds.IBData, bool]]:

        if not fromcb:

            if btsymbol in self.alldatas:
                return self.alldatas[btsymbol]

            data = self.store.getdata(dataname=btsymbol, rtbar=True, backfill_start=False)
            self.cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=5)
            self.alldatas[btsymbol] = data
            return data

        if btsymbol in self.alldatas:
            return self.alldatas[btsymbol], False

        data = self.store.getdata(dataname=btsymbol, rtbar=True, backfill_start=False)
        self.cerebro.resampledata(data, timeframe=bt.TimeFrame.Seconds, compression=5)
        data.reset()
        if self.cerebro._exactbars < 1:
            data.extend(size=self.cerebro.params.lookahead)
        data._start()
        if self.cerebro._dopreload:
            data.preload()
        self.alldatas[btsymbol] = data
        return data, True

    def add(self, xone):
        if xone.btsymbol not in self.xonesbybtsymbol:
            self.xonesbybtsymbol[xone.btsymbol] = list()

        self.xonesbybtsymbol[xone.btsymbol].append(xone)

    def run(self):
        try:
            self.cerebro = bt.Cerebro()

            self.store = bt.stores.IBStore(host=HOST, port=PORT)
            self.getdata("NIFTY50_IND_NSE")
            self.allxones = self.session.query(Xone).filter(
                or_(Xone.status == XoneStatus.CREATED, Xone.status == XoneStatus.OPEN)).all()

            self.openxones = self.session.query(Xone).filter(Xone.status == XoneStatus.OPEN).all()

            for xone in self.allxones:

                xone.start()
                xone.data = self.getdata(xone.btsymbol)

                for child in xone.children:
                    child.start()
                    child.data = self.getdata(child.btsymbol)

                self.add(xone)

            self.cerebro.setbroker(self.store.getbroker())

            self.cerebro.addstrategy(Grid, batman=self)

            self.cerebro.addsizer(MySizer)

            self.cerebro.run()

        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)

        input("run thread ends: ")


batman = BaTMan()
