from collections import OrderedDict
from datetime import datetime


SESSIONSTART = datetime.now().time().replace(hour=9, minute=15, second=0, microsecond=0)
SESSIONEND = datetime.now().time().replace(hour=14, minute=22, second=0, microsecond=0)


class AutoOrderedDict(OrderedDict):
    _closed = False

    def _close(self):
        self._closed = True
        for key, val in self.items():
            if isinstance(val, AutoOrderedDict):
                val._close()

    def _open(self):
        self._closed = False

    def __missing__(self, key):
        if self._closed:
            raise KeyError

        # value = self[key] = type(self)()
        value = self[key] = AutoOrderedDict()
        return value

    def __getattr__(self, key):
        if key.startswith('_'):
            raise AttributeError

        return self[key]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
            return

        self[key] = value

    # Define math operations
    def __iadd__(self, other):
        if type(self) != type(other):
            return type(other)() + other

        return self + other

    def __isub__(self, other):
        if type(self) != type(other):
            return type(other)() - other

        return self - other

    def __imul__(self, other):
        if type(self) != type(other):
            return type(other)() * other

        return self + other

    def __idiv__(self, other):
        if type(self) != type(other):
            return type(other)() // other

        return self + other

    def __itruediv__(self, other):
        if type(self) != type(other):
            return type(other)() / other

        return self + other


class SecType:
    IND = "IND"
    STK = "STK"
    FUT = "FUT"
    OPT = "OPT"


class XoneType:

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

    @classmethod
    def identify(cls, entry, stoploss):
        return cls.BULLISH if entry > stoploss else cls.BEARISH


class XoneStatus:

    CREATED = "CREATED"
    OPEN = "OPEN"
    STOPLOSS = "STOPLOSS"
    TARGET = "TARGET"
    MISSED = "MISSED"
    FAILED = "FAILED"
    ABORT = "ABORT"
    FORCECLOSED = "FORCE CLOSED"


class ChildType:

    BUY = "BUY"
    SELL = "SELL"

    @classmethod
    def invert(cls, _type):
        return cls.BUY if _type == cls.SELL else cls.SELL


class ChildStatus:

    CREATED = "CREATED"
    BOUGHT = "BOUGHT"
    SOLD = "SOLD"
    REJECTED = "REJECTED"
    MARGIN = "MARGIN"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"
    UNUSED = "UNUSED"
