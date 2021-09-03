from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, and_, or_, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.exc import StatementError, OperationalError

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
    trailing_stoploss = Column(Float)
    target = Column(Float)
    entry_hit = Column(Boolean, default=lambda: False)
    type = Column(String(8))
    created_at = Column(DateTime, default=datetime.now)
    opened_at = Column(DateTime, default=None)
    closed_at = Column(DateTime, default=None)
    status = Column(String(16), default=XoneStatus.CREATED)
    kid_count = Column(Integer)
    pnl = Column(Float, default=None)
    contract = relationship("Contract")
    children = relationship("Child", order_by="Child.id", back_populates='xone',
                                 cascade="all, delete, delete-orphan")
    def start(self, **kwargs):
        self.isbullish = True if self.type == XoneType.BULLISH else False
        self.orders = list()
        self.nextstatus = None
        self.close_children = False
        self.data = None


class Child(Base):
    __tablename__ = 'children'
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey('xones.id'))
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    symbol = Column(String(64))
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
    xone = relationship("Xone", back_populates="children")
    contract = relationship("Contract")

    def start(self, **kwargs):
        self.isbuy = True if self.type == ChildType.BUY else False
        self.data = None


class A(Base):
    __tablename__ = 'a'
    id = Column(Integer, primary_key=True, autoincrement=True)
    kid_count = Column(Integer, default=0)
    pnl = Column(Float, default=0)
    bs = relationship("B", order_by="B.id", back_populates='a', cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        pass


class B(Base):
    __tablename__ = 'b'
    id = Column(Integer, primary_key=True, autoincrement=True)
    aid = Column(Integer, ForeignKey('a.id'))
    pnl = Column(Float, default=0)
    a = relationship("A", back_populates="bs")

    def __init__(self, **kwargs):
        pass


class Db:

    def __init__(self):
        self.dialect = "mysql"
        self.driver = "pymysql"
        self.username = "root"
        self.password = "Soham19jain98"
        self.host = "localhost"
        self.port = "3306"
        self.database = "cerebelle"
        self.engine = create_engine(
            f"{self.dialect}+{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}",
            echo=False)
        self.tables = self.engine.table_names()
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.scoped_session = scoped_session(self.session_factory)
        self.session = self.scoped_session()