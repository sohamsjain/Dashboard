import datetime


# Session Time Boundry
SESSIONSTART = datetime.time(9, 15)
SESSIONEND = datetime.time(15, 30)
SESSIONSTOP = datetime.time(15, 29, 55)

YESTERDAY = datetime.datetime.now().date() - datetime.timedelta(days=5)

# Address
HOST = ""
PORT = 7496

# Resources
NSELOTSIZECSV = "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
