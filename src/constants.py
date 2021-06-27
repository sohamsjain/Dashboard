import datetime


# Session Time Boundry
SESSIONSTART = datetime.datetime.now().time().replace(hour=9, minute=15, second=0, microsecond=0)
SESSIONEND = datetime.datetime.now().time().replace(hour=14, minute=22, second=0, microsecond=0)

YESTERDAY = datetime.datetime.now().date() - datetime.timedelta(days=5)

# Address
HOST = "52.70.61.124"
PORT = 7497

# Resources
NSELOTSIZECSV = "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
