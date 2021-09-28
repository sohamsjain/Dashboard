from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, and_, or_, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import StatementError, OperationalError, IntegrityError

from src.util import *

Base = declarative_base()


class Contract(Base):
    __tablename__ = 'contracts'
    id = Column(Integer, primary_key=True)
    underlying = Column(String(16))
    sectype = Column(String(8))
    exchange = Column(String(8))
    currency = Column(String(8))
    symbol = Column(String(64), primary_key=True)
    strike = Column(Float)
    right = Column(String(8))
    expiry = Column(DateTime)
    multiplier = Column(Integer)
    btsymbol = Column(String(64))
    lotsize = Column(Integer)

    def start(self, **kwargs):
        pass


class Xone(Base):
    __tablename__ = 'xones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    symbol = Column(String(64))
    sectype = Column(String(8))
    btsymbol = Column(String(64))
    expiry = Column(DateTime)
    entry = Column(Float)
    stoploss = Column(Float)
    target = Column(Float)
    lastprice = Column(Float, default=None)
    type = Column(String(8))
    forced_entry = Column(Boolean, default=False)
    forced_exit = Column(Boolean, default=False)
    autonomous = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    entry_at = Column(DateTime, default=None)
    exit_at = Column(DateTime, default=None)
    opened_at = Column(DateTime, default=None)
    closed_at = Column(DateTime, default=None)
    status = Column(String(16), default=XoneStatus.CREATED)
    kid_count = Column(Integer)
    pnl = Column(Float, default=None)
    contract = relationship("Contract")
    children = relationship("Child", order_by="Child.id", back_populates='xone',
                                 cascade="all, delete-orphan")

    def start(self, **kwargs):
        self.isbullish = True if self.type == XoneType.BULLISH else False
        self.orders = list()
        self.nextstatus = None
        self.open_children = False
        self.close_children = False
        self.data = None

    def attributes(self):
        attributes = dict(symbol=self.symbol,
                          type=self.type,
                          entry=self.entry,
                          stoploss=self.stoploss,
                          target=self.target,
                          status=self.status,
                          pnl=self.pnl,
                          lastprice=self.lastprice,
                          sectype=self.sectype,
                          expiry=self.expiry)
        attributes = {k: v for k, v in attributes.items() if v}
        return attributes

    def notification(self):
        type = '+' if self.type == XoneType.BULLISH else '-'
        notif = f"{self.status}\n{self.symbol}:\t {self.lastprice}\n{type} {self.entry}  SL {self.stoploss}  T {self.target}"
        for child in self.children:
            ctype = '+' if child.type == ChildType.BUY else '-'
            notif += "\n______________________________\n"
            notif += f"{child.status}\n{child.symbol}:\t {child.lastprice}\n{ctype} {child.size}"
        return notif


class Child(Base):
    __tablename__ = 'children'
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey('xones.id'))
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    symbol = Column(String(64))
    lastprice = Column(Float, default=None)
    sectype = Column(String(8))
    btsymbol = Column(String(64))
    expiry = Column(DateTime)
    type = Column(String(8))
    size = Column(Integer, default=None)
    status = Column(String(16), default=ChildStatus.CREATED)
    created_at = Column(DateTime, default=datetime.now)
    opened_at = Column(DateTime, default=None)
    closed_at = Column(DateTime, default=None)
    filled = Column(Integer, default=0)
    buying_price = Column(Float, default=None)
    buying_cost = Column(Float, default=None)
    buying_commission = Column(Float, default=None)
    selling_price = Column(Float, default=None)
    selling_cost = Column(Float, default=None)
    selling_commission = Column(Float, default=None)
    pnl = Column(Float, default=None)
    contract = relationship("Contract")
    xone = relationship("Xone", back_populates="children")

    def start(self, **kwargs):
        self.isbuy = True if self.type == ChildType.BUY else False
        self.data = None

    def attributes(self):
        attributes = dict(symbol=self.symbol,
                          type=self.type,
                          size=self.size,
                          status=self.status,
                          filled=self.filled,
                          pnl=self.pnl,
                          lastprice=self.lastprice,
                          sectype=self.sectype,
                          expiry=self.expiry)
        attributes = {k: v for k, v in attributes.items() if v}
        return attributes

class Db:

    def __init__(self):
        self.dialect = "mysql"
        self.driver = "pymysql"
        self.username = "root"
        self.password = "Soham19jain98"
        self.host = "localhost"
        self.port = "3306"
        self.database = "cerebelle2"
        self.engine = create_engine(
            f"{self.dialect}+{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
            echo=False, pool_size=10, max_overflow=20)
        self.tables = self.engine.table_names()
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.scoped_session = scoped_session(self.session_factory)
