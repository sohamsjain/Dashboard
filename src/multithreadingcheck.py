from threading import Thread, current_thread
from src.models import *
import time

db = Db()
s = db.session
clist=list()


def f3(c):
    c.start()
    for i in c.invoices:
        i.start()


def f():
    ls = db.scoped_session()
    c = Customer(name="Soham")
    c.invoices = [Invoice(amount=5000)]
    ls.add(c)
    ls.commit()
    f3(c)
    clist.append(c)
    input(current_thread().name+": ")


def f2():
    global clist
    c1 = clist[0]
    input(current_thread().name+": ")


t = Thread(target=f).start()
time.sleep(5)
t2 = Thread(target=f2).start()
