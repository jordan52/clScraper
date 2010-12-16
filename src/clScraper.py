import xml.dom.minidom

import sys
import random
import time
import os.path
import pickle
import conf
import getopt
import urllib2
import smtplib
import sqlite3
import datetime


def main():
   parseCl('stlouis', 'msg')

def parseCl(city, category):

   document = xml.dom.minidom.parse(urllib2.urlopen('http://' + city + '.craigslist.org/' + category + '/index.rss'))

   conn = sqlite3.connect(conf.DB_FILENAME)
   f = open('clScraper.txt','w')

   runtimeId = start_runtime()
   cityId = get_id_by_prefix('city', city)
   categoryId = get_id_by_prefix('category', category)


   for item in document.getElementsByTagName('item'):
      title = item.getElementsByTagName('title')[0].firstChild.data
      link = item.getElementsByTagName('link')[0].firstChild.data
      description = item.getElementsByTagName('description')[0].firstChild.data
      listingDate = item.getElementsByTagName('dc:date')[0].firstChild.data
      listingLocation = ''

      # price/location splitter copied from Craigslist finder by Paul Mohr

      a = title.rfind("$") # Marker for price
      b = title.rfind("(") # Beginning marker for location
      c = title.rfind(")") # End marker for location

      if (a <> -1): # Seperate name and price
         listingPrice = title[a+1:len(title)]
         listingName = title[0:a]
      else: # If no price listed (bastards), it's just a name:
         listingName = title

      if (b <> -1) and (c <> -1):  #get the location
         listingLocation = title[b+1:c]
         listingName = listingName.replace(listingName[b:c+1], "")

      listingDateConverted = datetime.datetime(
         int(listingDate[0:4]),
         int(listingDate[5:7]),
         int(listingDate[8:10]),
         int(listingDate[11:13]),
         int(listingDate[14:16]),
         int(listingDate[17:19])
      ) # Date is in YYYY-MM-DD<T>HH:MM:SS-TZONE format retrieve month and date 

      conn.execute("insert into listing (title, name, location, price, link, description, listingDate,city_id,category_id,runtime_id) values (?,?,?,?,?,?,?,?,?,?)", (title,listingName,listingLocation,listingPrice,link,description,listingDateConverted,cityId,categoryId,runtimeId))

      print >>f, "----------------------Item-------------------------------"
      print >>f, title.encode('UTF8','replace')
      print >>f, listingName.encode('UTF8','replace')
      print >>f, listingPrice.encode('UTF8','replace')
      print >>f, listingLocation.encode('UTF8','replace')
      print >>f, description.encode('UTF8','replace')
      print >>f, link.encode('UTF8','replace')
      print >>f, listingDate.encode('UTF8','replace')
      print >>f, "------------------------------------------------------------------"
      print >>f, "\n"

   conn.commit()

def start_runtime():
   conn = sqlite3.connect(conf.DB_FILENAME)   
   cur = conn.cursor()
   cur.execute("insert into runtime (startTime) values (?);",(datetime.datetime.now(),))
   conn.commit()
   return cur.lastrowid


def get_id_by_prefix(table, prefixName):
   conn = sqlite3.connect(conf.DB_FILENAME)   
   cur = conn.cursor()
   cur.execute('select id from ' + table + " where prefix = '" + prefixName + "';")

   for row in cur:
     return row[0]

   #row doesn't exist
   cur.execute('insert into ' + table + "(prefix) values ('" + prefixName + "');")
   conn.commit()
   return cur.lastrowid
    
def usage():
    """Usage."""
    print """
Craigslist Mailer. Copyright (c) 2010 Jake Brukhman.
python craigslist-mailer.py
[-q,--queries <STRING,STRING,...>] -- search queries
[-m,--minAsk <INTEGER>] -- minimum price
[-M,--maxAsk <INTEGER>] -- maximum price
[-b,--bedrooms <INTEGER>] -- number of bedrooms
[-u,--url <STRING>] -- override the url
[-s,--batch-size <INTEGER>] -- override the batch size (should be >= 1)
"""

def get_args():
    global QUERIES, MIN_ASK, MAX_ASK, BEDROOMS
    """Get the commandline arguments."""
    opts,args = getopt.getopt(sys.argv[1:],\
            "q:m:M:b:u:s:h", ['help', 'query=', 'minAsk=', 'maxAsk=', 'bedrooms=', 'url=', 'batch-size='])
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        if opt in ('-q', '--queries'):
            QUERIES=arg.split(',')
        if opt in ('-m', '--minAsk'):
            MIN_ASK=str(int(arg)) # checks for integer
        if opt in ('-M', '--maxAsk'):
            MAX_ASK=str(int(arg))
        if opt in ('-b', '--bedrooms'):
            BEDROOMS=str(int(arg))
        if opt in ('-u', '--url'):
            conf.CRAIGS_URL=arg
        if opt in ('-s' '--batch-size'):
            arg = int(arg) # raises ValueError if not integer
            if arg<1: # BATCH_SIZE must be >= 1
                raise ValueError
            conf.BATCH_SIZE=arg

def check_conf():
    """Make sure configuration variables are set."""
    # check SMTP credentials
    try:
        conf.SMTP_USER
        conf.SMTP_PASS
        conf.SMTP_SERVER
    except AttributeError:
        print "SMTP credentials are missing."
        sys.exit(2)
    
    try:
        conf.RECIPIENTS
    except AttributeError:
        print "RECIPIENTS variable is missing."
        sys.exit(2)
        
    try:
        conf.BATCH_SIZE
        conf.CACHE_FILE
        conf.CACHE_SIZE
    except AttributeError:
        print "One of mandatory variables BATCH_SIZE, CACHE_SIZE, or CACHE_FILE is missing."
        sys.exit(2)

def check_db():
   #copied from http://www.doughellmann.com/PyMOTW/sqlite3/

   db_is_new = not os.path.exists(conf.DB_FILENAME)

   conn = sqlite3.connect(conf.DB_FILENAME)
   if db_is_new:
      print 'Creating schema'
      f = open(conf.SCHEMA_FILENAME, 'rt')
      schema = f.read()
      conn.executescript(schema)


#
#
#
if __name__=='__main__':
    try:
        check_conf()
        get_args()
        check_db()
        main()
    except ValueError, strerror:
        print "Error: ", strerror
        usage()
    except getopt.GetoptError:
        usage()
    except KeyboardInterrupt:
        print "Goodbye."
        sys.exit(0)
    sys.exit(2)
