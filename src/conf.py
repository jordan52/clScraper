'''
Created on Dec 14, 2010

very much copied from craigslist-mailer/

@author: jordan woerndle
'''

#
# SET THE SMTP CREDENTIALS
#
SMTP_USER ='username'
SMTP_PASS ='password'
SMTP_SERVER ='smtp.gmail.com'

#
# SET THE RECIPIENTS (COLON SEPARATED)
#
RECIPIENTS ='jordan52@gmail.com;you@gmail.com'

#
# OTHER VARIABLES
#
CACHE_FILE ='titles.cache' # title of the cache file
CACHE_SIZE =1000 # maximum size of the cache
SENDER ='jordan52@gmail.com' # the e-mail sender (may not work with all SMTP providers e.g. gmail)
BATCH_SIZE =1 # minimum number of listings to send at one time
DB_FILENAME='clScraper.db'
SCHEMA_FILENAME='clScraperSchema.sql'
CITIES=['stlouis','columbiamo']
CATEGORIES=['msg','sys']
