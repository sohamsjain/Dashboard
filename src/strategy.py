from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from queue import Queue
import backtrader as bt
from src.models import *
from src.constants import SESSIONSTOP


class Grid(bt.Strategy):
    params = (
        ('maxpos', 5),
        ('batman', None)
    )

    def __init__(self):
        self.batman = self.p.batman
        self.childrenbyorder = dict()
        self.openordercount = 0
        self.sessionq = Queue()
        self.db = self.batman.db
        self.session = self.batman.session
        self.addxone = self.batman.addxone
        self.removexone = self.batman.removexone
        self.addchild = self.batman.addchild
        self.removechild = self.batman.removechild
        self.openxones = self.batman.openxones
        self.allxones = self.batman.allxones
        self.allchildren = self.batman.allchildren

    def notify_order(self, order):

        if order.status in [order.Submitted, order.Accepted, order.Partial]:
            return

        try:
            child = self.childrenbyorder[order.ref]
            self.childrenbyorder.pop(order.ref)
        except KeyError as k:
            print(k)
            return

        if order.status == order.Completed:

            if order.isbuy():

                child.buying_price = order.executed.price
                child.buying_cost = order.executed.value
                child.buying_commission = order.executed.comm

                if child.isbuy:
                    child.filled += order.executed.size
                    child.status = ChildStatus.BOUGHT
                    child.opened_at = datetime.now()
                else:
                    child.filled += order.executed.size
                    child.status = ChildStatus.SQUAREDOFF
                    child.closed_at = datetime.now()
                    child.pnl = child.selling_cost - child.buying_cost

            else:

                child.selling_price = order.executed.price
                child.selling_cost = order.executed.value
                child.selling_commission = order.executed.comm

                if child.isbuy:
                    child.filled += order.executed.size
                    child.status = ChildStatus.SQUAREDOFF
                    child.closed_at = datetime.now()
                    child.pnl = child.selling_cost - child.buying_cost
                else:
                    child.filled += order.executed.size
                    child.status = ChildStatus.SOLD
                    child.opened_at = datetime.now()

        elif order.status == order.Canceled:
            child.status = ChildStatus.CANCELLED
        elif order.status == order.Margin:
            child.status = ChildStatus.MARGIN
        elif order.status == order.Rejected:
            child.status = ChildStatus.REJECTED

        xone = child.xone
        xone.orders.remove(order)

        if xone.orders == [None]:  # All child orders processed

            if xone.status in XoneStatus.PENDING:

                self.openordercount -= 1

                xone.status = XoneStatus.ENTRY
                xone.opened_at = datetime.now()
                self.openxones.append(xone)

                for child in xone.children:
                    if child.status in [ChildStatus.MARGIN, ChildStatus.REJECTED]:
                        xone.status = XoneStatus.ABORT
                        break

            elif xone.status in XoneStatus.OPEN:
                xone.closed_at = datetime.now()
                xone.pnl = sum([c.pnl for c in xone.children if c.pnl is not None])
                xone.status = xone.nextstatus
                self.removexone(xone)
                self.openxones.remove(xone)

            elif xone.status == XoneStatus.ABORT:
                xone.closed_at = datetime.now()
                xone.pnl = sum([c.pnl for c in xone.children if c.pnl is not None])
                xone.status = XoneStatus.FORCECLOSED
                self.removexone(xone)
                self.openxones.remove(xone)

            xone.orders.clear()

        self.session.commit()

    def notify_trade(self, trade):
        pass

    def notify_data(self, data, status, *args, **kwargs):
        print(data._dataname, data._getstatusname(status))

    def notify_store(self, msg, *args, **kwargs):
        print(msg)

    def notify_cashvalue(self, cash, value):
        # print("Cash: ", cash, "Value", value)
        pass

    def notify_fund(self, cash, value, fundvalue, shares):
        # print(cash, value, fundvalue, shares)
        pass

    def next(self):

        self.session.commit()

        for xone in self.allxones:
            data = xone.data

            try:  # In case a new datafeed is added, it may not produce a bar
                xone.lastprice = xone.data.close[0]  # This is a work around to eliminate unnecessary IndexError
                for child in xone.children:  # Must apply for xone.data as well as child.data
                    child.lastprice = child.data.close[0]
            except IndexError:
                continue

            if xone.orders:  # Skip an iteration until pending orders are completed
                continue

            if xone.status in XoneStatus.PENDING:

                if xone.isbullish:
                    if (xone.status == XoneStatus.ENTRYHIT) and (data.high[0] >= xone.target):
                        xone.status = XoneStatus.MISSED
                        for child in xone.children:
                            child.status = ChildStatus.UNUSED
                        self.removexone(xone)
                        continue
                    if data.low[0] < xone.stoploss:
                        xone.status = XoneStatus.FAILED
                        for child in xone.children:
                            child.status = ChildStatus.UNUSED
                        self.removexone(xone)
                        continue
                    if data.low[0] <= xone.entry:
                        if xone.status == XoneStatus.CREATED:
                            xone.status = XoneStatus.ENTRYHIT
                            xone.entry_at = datetime.now()
                        if xone.autonomous:
                            xone.open_children = True

                else:
                    if (xone.status == XoneStatus.ENTRYHIT) and (data.low[0] <= xone.target):
                        xone.status = XoneStatus.MISSED
                        for child in xone.children:
                            child.status = ChildStatus.UNUSED
                        self.removexone(xone)
                        continue
                    if data.high[0] > xone.stoploss:
                        xone.status = XoneStatus.FAILED
                        for child in xone.children:
                            child.status = ChildStatus.UNUSED
                        self.removexone(xone)
                        continue
                    if data.high[0] >= xone.entry:
                        if xone.status == XoneStatus.CREATED:
                            xone.status = XoneStatus.ENTRYHIT
                            xone.entry_at = datetime.now()
                        if xone.autonomous:
                            xone.open_children = True

                if xone.open_children or xone.forced_entry:
                    xone.open_children = False
                    if not xone.children:
                        continue
                    if (len(self.openxones) + self.openordercount) < self.p.maxpos:
                        self.openordercount += 1
                        for child in xone.children:
                            size = child.size
                            if child.isbuy:
                                order = self.buy(data=child.data, size=size)
                            else:
                                order = self.sell(data=child.data, size=size)
                            xone.orders.append(order)
                            self.childrenbyorder[order.ref] = child
                        xone.orders.append(None)

            elif xone.status in XoneStatus.OPEN:

                if xone.isbullish:
                    if data.low[0] < xone.stoploss:
                        if xone.status == XoneStatus.ENTRY:
                            xone.status = XoneStatus.STOPLOSSHIT
                            xone.nextstatus = XoneStatus.STOPLOSS
                            xone.exit_at = datetime.now()

                        if xone.autonomous:
                            xone.close_children = True

                    elif data.high[0] >= xone.target:
                        if xone.status == XoneStatus.ENTRY:
                            xone.status = XoneStatus.TARGETHIT
                            xone.nextstatus = XoneStatus.TARGET
                            xone.exit_at = datetime.now()

                        if xone.autonomous:
                            xone.close_children = True

                else:
                    if data.high[0] > xone.stoploss:
                        if xone.status == XoneStatus.ENTRY:
                            xone.status = XoneStatus.STOPLOSSHIT
                            xone.exit_at = datetime.now()

                        if xone.autonomous:
                            xone.nextstatus = XoneStatus.STOPLOSS
                            xone.close_children = True

                    elif data.low[0] <= xone.target:
                        if xone.status == XoneStatus.ENTRY:
                            xone.status = XoneStatus.TARGETHIT
                            xone.exit_at = datetime.now()

                        if xone.autonomous:
                            xone.nextstatus = XoneStatus.TARGET
                            xone.close_children = True

                if xone.close_children or xone.forced_exit:
                    xone.close_children = False
                    for child in xone.children:
                        if child.isbuy:
                            order = self.sell(data=child.data, size=child.filled)
                        else:
                            order = self.buy(data=child.data, size=child.filled)
                        xone.orders.append(order)
                        self.childrenbyorder[order.ref] = child
                    xone.orders.append(None)

            elif xone.status == XoneStatus.ABORT:
                for child in xone.children:
                    if child.filled > 0:
                        if child.status == ChildStatus.BOUGHT:
                            order = self.sell(data=child.data, size=child.filled)
                        else:
                            order = self.buy(data=child.data, size=child.filled)
                        xone.orders.append(order)
                        self.childrenbyorder[order.ref] = child
                if len(xone.orders):
                    xone.orders.append(None)
                else:
                    xone.closed_at = datetime.now()
                    xone.pnl = sum([c.pnl for c in xone.children if c.pnl is not None])
                    xone.status = XoneStatus.FORCECLOSED
                    self.removexone(xone)
                    self.openxones.remove(xone)

            else:
                self.removexone(xone)

        self.session.commit()

        self.handlerequests()

        if self.datas[0].datetime.time(0) >= SESSIONSTOP:
            self.cerebro.runstop()

    def handlerequests(self):

        while not self.sessionq.empty():
            message = self.sessionq.get()
            head = message['head']
            body = message['body']
            responseq: Queue = message['responseq']

            if head == RequestType.ADDXONE:
                xone: Xone = body

                try:
                    self.session.add(xone)
                    self.addxone(xone)
                    self.session.commit()
                except Exception as e:
                    print(e)
                    responseq.put(ResponseType.ADDXONEFAILURE)
                    continue
                responseq.put(ResponseType.ADDXONESUCCESS)
                responseq.put(xone.id)
                continue

            if head == RequestType.DELETEXONE:
                try:
                    xone_id = body
                    xone = self.session.query(Xone).get(xone_id)
                    if xone.orders:
                        print(f"Xone {xone_id} has open orders, it cannot be deleted")
                        responseq.put(ResponseType.DELETEXONEFAILURE)
                        continue
                    self.removexone(xone)
                    self.session.delete(xone)
                    self.session.commit()
                except Exception as e:
                    print(e)
                    responseq.put(ResponseType.DELETEXONEFAILURE)
                    continue
                responseq.put(ResponseType.DELETEXONESUCCESS)
                continue

            if head == RequestType.ADDCHILD:
                try:
                    child: Child = body['child']
                    xone_id = body['xone_id']
                    xone = self.session.query(Xone).get(xone_id)
                    if xone.orders:
                        print(f"Xone {xone_id} has open orders, a child can not be added to it")
                        responseq.put(ResponseType.ADDCHILDFAILURE)
                        continue
                    xone.children.append(child)
                    xone.kid_count += 1
                    self.addchild(child)
                    self.session.commit()
                except Exception as e:
                    print(e)
                    responseq.put(ResponseType.ADDCHILDFAILURE)
                    continue
                responseq.put(ResponseType.ADDCHILDSUCCESS)
                responseq.put(child.id)
                continue

            if head == RequestType.DELETECHILD:
                try:
                    child_id = body
                    child = self.session.query(Child).get(child_id)
                    xone = child.xone
                    if xone.orders:
                        print(f"The child's xone has open orders, it can not be deleted")
                        responseq.put(ResponseType.DELETECHILDFAILURE)
                        continue
                    xone.children.remove(child)
                    xone.kid_count -= 1
                    self.removechild(child)
                    # self.batman.session.delete(child)  # Redundant statement. orphan child gets deleted by default
                    self.session.commit()
                except Exception as e:
                    print(e)
                    responseq.put(ResponseType.DELETECHILDFAILURE)
                    continue
                responseq.put(ResponseType.DELETECHILDSUCCESS)
                continue

    def start(self):
        self.batman.market = True
        self.batman.sessionq = self.sessionq

    def stop(self):
        self.batman.market = False
        self.batman.sessionq = None
