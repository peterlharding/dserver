#!/usr/bin/env python

import httplib
import random
import urllib

#-------------------------------------------------------------------------------

HOST_STR  = 'dserver:9567'
PORT      = 9567

params  = urllib.urlencode({'aaa' : 1})

headers = {
  'Content-Type' : 'text/html; charset=utf-8',
}

get_headers = {
   'Accept-Encoding'    : 'gzip, deflate',
   'Accept'             : '*/*',
   'Accept-Language'    : 'en-au',
   'Host'               : HOST_STR,
   'Connection'         : 'Keep-Alive',
   'User-Agent'         : 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727'
}



#-------------------------------------------------------------------------------

def tst_indexed(no):
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETI|3|%d' % no

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

def tst_indexer():
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETN|0'

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

def tst_keyed(key):
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETK|6|%s' % key

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

def tst_keyed_random(key):
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETKR|5|%s' % key

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

def tst_barcodes(key):
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETB|0|%s' % key

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

def get_run_no():
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETN|1'

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

# tst_indexer()
# tst_csv()
# tst_indexed(5)
# tst_keyed()
# tst_barcodes('EF-89-CA')
# tst_keyed_random("AUPERB")
get_run_no()


#-------------------------------------------------------------------------------

