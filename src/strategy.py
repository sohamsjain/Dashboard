from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from queue import Queue
import backtrader as bt
from src.models import *


class Grid(bt.Strategy):
    params = (
        ('maxpos', 5),
        ('batman', None)
    )

    def __init__(self):
        self.batman = self.p.batman
        self.order = None
        self.childrenbyorder = dict()
        self.openordercount = 0
        self.sessionq = Queue()

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
                    child.status = ChildStatus.CLOSED
                    child.closed_at = datetime.now()
                    child.pnl = child.selling_cost - child.buying_cost

            else:

                child.selling_price = order.executed.price
                child.selling_cost = order.executed.value
                child.selling_commission = order.executed.comm

                if child.isbuy:
                    child.filled += order.executed.size
                    child.status = ChildStatus.CLOSED
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

            if xone.status == XoneStatus.CREATED:

                self.openordercount -= 1

                xone.status = XoneStatus.OPEN
                xone.opened_at = datetime.now()
                self.batman.openxones.append(xone)

                for child in xone.children:
                    if child.status in [ChildStatus.MARGIN, ChildStatus.REJECTED]:
                        xone.status = XoneStatus.ABORT
                        break

            elif xone.status == XoneStatus.OPEN:
                xone.closed_at = datetime.now()
                xone.pnl = sum([c.pnl for c in xone.children if c.pnl is not None])
                xone.status = xone.nextstatus
                self.batman.remove(xone)
                self.batman.openxones.remove(xone)

            elif xone.status == XoneStatus.ABORT:
                xone.closed_at = datetime.now()
                xone.pnl = sum([c.pnl for c in xone.children if c.pnl is not None])
                xone.status = XoneStatus.FORCECLOSED
                self.batman.remove(xone)
                self.batman.openxones.remove(xone)

            xone.orders.clear()

        self.batman.session.commit()

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

        while not self.sessionq.empty():
            xone = self.sessionq.get()
            self.batman.add(xone)
            try:
                if xone.data._dataname not in [d._dataname for d in self.datas]:
                    self.datas.append(xone.data)
            except Exception as e:
                print(e)

        for data in self.datas:
            btsymbol = data._dataname

            try:
                xonesofakind = self.batman.xonesbybtsymbol[btsymbol]
            except KeyError as ke:
                continue

            for xone in xonesofakind:

                if xone.orders:
                    continue

                try:
                    xd = xone.data.close[0]
                    for child in xone.children:
                        cd = child.data.close[0]
                except IndexError:
                    continue

                if xone.status == XoneStatus.CREATED:
                    if xone.isbullish:
                        if xone.entry_hit and data.high[0] >= xone.target:
                            xone.status = XoneStatus.MISSED
                            for child in xone.children:
                                child.status = ChildStatus.UNUSED
                            self.batman.remove(xone)
                            continue
                        if data.low[0] < xone.stoploss:
                            xone.status = XoneStatus.FAILED
                            for child in xone.children:
                                child.status = ChildStatus.UNUSED
                            self.batman.remove(xone)
                            continue
                        if data.low[0] <= xone.entry:
                            xone.entry_hit = True
                            if (len(self.batman.openxones) + self.openordercount) < self.p.maxpos:
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

                    else:
                        if xone.entry_hit and data.low[0] <= xone.target:
                            xone.status = XoneStatus.MISSED
                            for child in xone.children:
                                child.status = ChildStatus.UNUSED
                            self.batman.remove(xone)
                            continue
                        if data.high[0] > xone.stoploss:
                            xone.status = XoneStatus.FAILED
                            for child in xone.children:
                                child.status = ChildStatus.UNUSED
                            self.batman.remove(xone)
                            continue
                        if data.high[0] >= xone.entry:
                            xone.entry_hit = True
                            if (len(self.batman.openxones) + self.openordercount) < self.p.maxpos:
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

                elif xone.status == XoneStatus.OPEN:

                    if xone.isbullish:
                        if data.low[0] < xone.stoploss:
                            xone.nextstatus = XoneStatus.STOPLOSS
                            xone.close_children = True

                        elif data.high[0] >= xone.target:
                            xone.nextstatus = XoneStatus.TARGET
                            xone.close_children = True

                    else:
                        if data.high[0] > xone.stoploss:
                            xone.nextstatus = XoneStatus.STOPLOSS
                            xone.close_children = True

                        elif data.low[0] <= xone.target:
                            xone.nextstatus = XoneStatus.TARGET
                            xone.close_children = True

                    if xone.close_children:
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
                        self.batman.remove(xone)
                        self.batman.openxones.remove(xone)

                else:
                    self.batman.remove(xone)

        self.batman.session.commit()

    def stop(self):
        self.batman.market = False
        self.batman.sessionq = None

    def start(self):
        self.batman.market = True
        self.batman.sessionq = self.sessionq
