#!/usr/bin/env python
#
#       Author:  Peter Harding  <plh@performiq.com.au>
#                PerformIQ Pty. Ltd.
#                Level 6, 170 Queen Street,
#                MELBOURNE, VIC, 3000
# 
#                Phone:   03 9641 2222
#                Fax:     03 9641 2200
#                Mobile:  0418 375 085
# 
#          Copyright (C) 1994-2008, Peter Harding
#                        All rights reserved
#
#---------------------------------------------------------------------
"""
Purpose:

  Python implementation of DataServer client API

  Usage:

     ds = client.Connection(port=PORT)

     if (ds == None):
        print("Connection to data server failed - is data server process running?\n")
        return 1

     (type_ref, attributes)  = ds.RegisterType(table_name)

  Then one of:

    a)  Pulling data:

          if Hashed:
              sp  = ds.GetHashed(type_ref, hash_key)
          elif Keyed:
              sp  = ds.GetNextKeyed(type_ref, key)
          elif Indexed:
              sp  = ds.GetIndexed(type_ref, index)
          else:
              sp  = ds.GetNext(type_ref)

    a)  Storing data:

          if Keyed:
             ds.StoreKeyedData(type_ref, key, store_data)
          else:
             ds.StoreCsvData(type_ref, store_data)

   Notes:

   i)    For an indexed type the atributes returned are:

         {
           'type'     : 'Indexed',
           'no_items' : <NO>
         }


"""
#---------------------------------------------------------------------

import os
import re
import sys
import copy
import getopt
import marshal

#---------------------------------------------------------------------

from socket import *        # portable socket interface plus constants

#---------------------------------------------------------------------

__id__            = "@(#) [2.1.0] client.py 2008-07-15"
__version__       = re.search(r'.*\[([^\]]*)\].*', __id__).group(1)

HOST              = 'localhost'
PORT              = 9578

debug_level       = 0
verbose_flg       = False

#---------------------------------------------------------------------

class Connection:
   DELIM          = ','
   ServerHostname = None    # server name, default to 'localhost'
   ServerPort     = None    # non-reserved port used by the server
   sockobj        = None
   Fields         = None

   def __init__(self, server=HOST, port=PORT, debug=0):
      global debug_level

      "Initialize TCP/IP socket object and make connection to server:port"

      self.ServerHostname = server
      self.ServerPort     = port
      debug_level         = debug

      self.sockobj = socket(AF_INET, SOCK_STREAM) 

      try:
         self.sockobj.connect((self.ServerHostname, self.ServerPort))
      except SocketError, e:
         sys.stderr.write('[client]  Connect failed: %s\n' % str(e))
         sys.exit(1)

      msg        = "INIT|Python"

      attributes = self.Get(msg)

#      try:
#         attributes = self.Get(msg)
#      except e:
#          sys.stderr.write('[client]  Get failed: %s\n' % str(e))
#          sys.exit(1)

      self.attributes     = marshal.loads(attributes)
      self.sources        = {}

      if debug_level > 0:  print 'Connection.attributes -> "%s"' % self.attributes

   #------------------------------------------------------------------

   def Get(self, s):
      "Send s to server and get back response"

      if self.sockobj != None:
         self.sockobj.send(s)

         data = self.sockobj.recv(1024)

         if debug_level > 0: print '[Client::Get]  Sent:  "%s"  Received: "%s"' % (s, data)

         return data
      else:
         return None

   #------------------------------------------------------------------

   def Close(self):
      "close socket to send eof to server"

      if self.sockobj != None:
         self.sockobj.close()
         self.sockobj = None

   #------------------------------------------------------------------

   def RegisterType(self, type):
      msg    = "REG|%s" % type

      # Should I really be using a try: here?   - PLH 2008-05-10

      try:
         response = self.Get(msg)
      except:
         type_ref = -1

      (type_ref, attributes) = response.split('|', 1)
      type_ref               = int(type_ref)
      attributes             = marshal.loads(attributes)

      self.sources[type_ref] = attributes

      return (type_ref, attributes)

   #------------------------------------------------------------------

   def GetNext(self, type_ref):
      msg      = "GETN|%d" % type_ref
      csv_data = self.Get(msg)
      data     = csv_data.split(self.DELIM)

      return data

   #------------------------------------------------------------------

   def GetHashed(self, type_ref, key):
      msg      = "GETH|%d|%s" % (type_ref, key)
      csv_data = self.Get(msg)
      data     = csv_data.split(self.DELIM)

      return data

   #------------------------------------------------------------------

   def GetNextKeyed(self, type_ref, key):
      msg      = "GETK|%d|%s" % (type_ref, key)
      csv_data = self.Get(msg)
      data     = csv_data.split(self.DELIM)

      return data

   #------------------------------------------------------------------

   def GetRandomKeyed(self, type_ref, key):
      msg      = "GETKR|%d|%s" % (type_ref, key)
      csv_data = self.Get(msg)
      data     = csv_data.split(self.DELIM)

      return data

   #------------------------------------------------------------------

   def GetIndexed(self, type_ref, idx):
      msg      = "GETI|%s|%s" % (type_ref, idx)
      csv_data = self.Get(msg)
      data     = csv_data.split(self.DELIM)

      return data

   #------------------------------------------------------------------

   def StoreCsvData(self, type_ref, data):
      msg     = "STOC|%d|%s" % (type_ref, data)
      reply   = self.Get(msg)

      try:
         rc = int(reply)
      except:
         rc = -1

      return rc

   #------------------------------------------------------------------

   def StoreKeyedData(self, type_ref, key_ref, data):
      msg     = "STOK|%d|%s|%s" % (type_ref, key_ref, data)
      reply   = self.Get(msg)

      try:
         rc = int(reply)
      except:
         rc = -1

      return rc

   #------------------------------------------------------------------

   def GetField(self, type_ref, i):
      if (i < len(self.Field[i])):
         return self.Field[i]
      else:
         return None

#---------------------------------------------------------------------

def main(argv):
   global debug_level
   global verbose_flg
   global PORT

   try:
      opts, args = getopt.getopt(argv, "dhD:p:vV?")
   except getopt.error, msg:
      print __doc__,
      return 1

   for o, a in opts:
      if o == '-d':
         debug_level       += 1
      elif o == '-D':
         debug_level        = int(a)
      elif o == '-p':
         PORT               = int(a)
      elif o == '-v':
         verbose_flg        = True
      elif o == '-V':
         print "Version: %s" % __version__
         return 0
      elif o in ( '-h', '-?'):
         print __doc__
         return 0

#---------------------------------------------------------------------

if __name__ == '__main__' or __name__ == sys.argv[0]:
   sys.exit(main(sys.argv[1:]))

#---------------------------------------------------------------------

"""
Revision History:

     Date     Who   Description
   --------   ---   --------------------------------------------------
   20031014   plh   Initial implementation
   20080510   plh   Refactored as client and Connection rather than dcl

Problems to fix:

To Do:

Issues:

"""
