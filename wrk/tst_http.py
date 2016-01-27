#!/usr/bin/env python

import httplib
import random
import urllib

#-------------------------------------------------------------------------------

HOST_STR  = 'localhost:9575'
PORT      = 9575

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

def do_indexed():
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETI|0|%d' % random.randint(0, 999)

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

def do_keyed():
   conn = httplib.HTTPConnection(HOST_STR)

   URL    = '/?msg=GETK|6|a101'

   conn.request("GET", URL, None, get_headers)

   rc = conn.getresponse()

   # print rc.__dict__
   print rc.status, rc.reason
   # print rc.msg

   data = rc.read()

   print "Data: [%s]" % data

   conn.close()

#-------------------------------------------------------------------------------

# do_indexed()
do_keyed()


