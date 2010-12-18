# code started with craigslist-mailer.py but doesn't much resemble it anymore

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

def main(conn):

   while True:
      for city in conf.CITIES:
         for cat in conf.CATEGORIES:
            parseCl(conn, city, cat)
            get_prices(conn)
            #sleep_time = random.randint(6,6*2)
            #print "Sleeping %d seconds before next retrieve..." % sleep_time
            #time.sleep(sleep_time)
      sleep_time = random.randint(60,60*5)
      print "Sleeping %d seconds before next retrieve..." % sleep_time
      time.sleep(sleep_time)

def parseCl(conn, city, category):
   url = 'http://' + city + '.craigslist.org/' + category + '/index.rss'
   try:
      document = xml.dom.minidom.parse(urllib2.urlopen(url))
   except urllib2.URLError:
      print 'unable to open ' + url
      return
   except xml.parsers.expat.ExpatError:
      print 'unable to parse rss feed!'
      return

   runtimeId = start_runtime(conn)
   cityId = get_id_by_prefix(conn, 'city', city)
   categoryId = get_id_by_prefix(conn,'category', category)

   for item in document.getElementsByTagName('item'):
      title = item.getElementsByTagName('title')[0].firstChild.data
      link = item.getElementsByTagName('link')[0].firstChild.data
      description = item.getElementsByTagName('description')[0].firstChild.data
      listingDate = item.getElementsByTagName('dc:date')[0].firstChild.data
      listingLocation = ''
      listingPrice = ''

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

      # make sure one isn't already in there that has the same title.
      cur = conn.cursor()
      cur.execute(('select id from listing where name = ?'), (listingName,))
      listingExists = False
      for row in cur:
         listingExists = True

      if not listingExists:
         conn.execute("insert into listing (title, name, location, price, link, description, listingDate,city_id,category_id,runtime_id) values (?,?,?,?,?,?,?,?,?,?)", (title,listingName,listingLocation,listingPrice,link,description,listingDateConverted,cityId,categoryId,runtimeId))
   stop_runtime(conn,runtimeId)
   conn.commit()

def get_prices(conn):
   cur = conn.cursor()
   cur.execute("select id, title, name, description from listing where id not in (select listing_id from analyzed);")
   for row in cur:
      print ' getting price for ' + row[1]
      get_price(conn,row)

def get_price(conn,row):
   listing_id = row[0]

   #theoretically, we successfully got the pricing data, so add a row to analyzed.
   conn.execute("insert into analyzed (listing_id,analyzedDate) values (?, ?);",(listing_id,datetime.datetime.now(),))

def start_runtime(conn):
   cur = conn.cursor()
   cur.execute("insert into runtime (startTime) values (?);",(datetime.datetime.now(),))
   return cur.lastrowid

def stop_runtime(conn,id):
   cur = conn.cursor()
   cur.execute("update runtime set endTime = ? where id = ?;",(datetime.datetime.now(),id,))

def get_id_by_prefix(conn,table, prefixName):
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
Craigslist Scaper. Copyright (c) 2010 Jordan Woerndle.
python clScraper.py
[-q,--queries <STRING,STRING,...>] -- search queries
[-m,--minAsk <INTEGER>] -- minimum price
[-M,--maxAsk <INTEGER>] -- maximum price
[-u,--url <STRING>] -- override the url
"""

def get_args():
    global QUERIES, MIN_ASK, MAX_ASK
    """Get the commandline arguments."""
    opts,args = getopt.getopt(sys.argv[1:],\
            "q:m:M:u:s:h", ['help', 'query=', 'minAsk=', 'maxAsk=', 'url=', 'batch-size='])
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

   if db_is_new:
      print 'Creating schema'
      f = open(conf.SCHEMA_FILENAME, 'rt')
      schema = f.read()
      conn = sqlite3.connect(conf.DB_FILENAME)

      conn.executescript(schema)
      conn.commit()
      conn.close()

#
#
#
if __name__=='__main__':
    try:
        check_conf()
        get_args()
        
        check_db()

        conn = sqlite3.connect(conf.DB_FILENAME)
        main(conn)
    except ValueError, strerror:
        print "Error: ", strerror
        usage()
    except getopt.GetoptError:
        usage()
    except KeyboardInterrupt:
        conn.close()
        print "Goodbye."
        sys.exit(0)
    sys.exit(2)
