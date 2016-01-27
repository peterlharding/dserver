#!/usr/bin/env python
#
#       Author:  Peter Harding  <plh@pha.com.au>
#                PerformIQ Pty. Ltd.
# 
#                Mobile:  0418 375 085
# 
#          Copyright (C) 1994-2008, Peter Harding
#                        All rights reserved
#
#
#---------------------------------------------------------------------
"""
Test example of use of Data Server.

  Usage: 

    # tst.py -t <table> [-k <key>]

      The '-t <table>' option is used to specify the name
      of the table to query

      The '-i <index>' specifies the index for the indexed
      data type.  Indexes may be either an integer which
      reurns the ith element of a string - in which case
      the key to the data set must be a string.

      The '-k <key>'   specifies the key for the keyed data
      type


"""
#---------------------------------------------------------------------

import os
import re
import sys
import getopt

import client

#---------------------------------------------------------------------

__id__            = "@(#) [2.2.0] tst.py 2008-07-15"
__version__       = re.search(r'.*\[([^\]]*)\].*', __id__).group(1)

#---------------------------------------------------------------------

HOST              = '10.6.5.194'
HOST              = 'dserver'
HOST              = '127.0.0.1'
PORT              = 9578
ENVIRONMENT       = 'SVT'

source_name       = "Test"

hashed            = False
hash_key          = None

indexed           = False
index             = None

keyed             = False
key               = None

store_flg         = False
store_data        = None

debug_level       = 0
term_flg          = False
verbose_flg       = False

ds_dir            = None
data_dir          = None

CONFIGFILE        = "dserver.ini"

sources           = {}

DELIMITER         = 'delimiter'

#=====================================================================

class Source:
   Count    = 0
   Valid    = False
   Name     = None
   Type     = None
   Idx      = None
   Data     = None

   def __init__(self, name, environment, source_type, attributes={}, delimiter=None):
      self.Name        = name
      self.Environment = environment
      self.Type        = source_type
      self.File        = "%s/%s.dat" % (environment, name)
      self.Used        = "%s/tmp/%s.used" % (environment, name)
      self.Stored      = "%s/tmp/%s.stored" % (environment, name)
      self.Comments    = []

      if debug_level > 2:
         print '[tst]  Name: "%s"  Type: "%s"  Attributes: "%s"' %\
             (self.Name, self.Type, repr(attributes))

      if delimiter:
         self.Delimiter  = delimiter
      elif attributes.has_key(DELIMITER):
         self.Delimiter  = attributes[DELIMITER]
      else:
         self.Delimiter  = ','

      if self.Type != 'Indexer' and not os.path.exists(self.File):
         print "[dserver]  Bad source_type [%s] in [%s]" % (source_type, self.File)

      self.Size        = 0
      self.Attributes  = {
                            'Type'       : self.Type,
                            'Delimiter'  : self.Delimiter,
                            'Size'       : 0
                         }

   #------------------------------------------------------------------

   def __str__(self):
      s = "%-22s %-10s" % (self.Name, self.Type)

      return s

#=====================================================================

def read_config():
   global PORT, ENVIRONMENT

   # Have cd'd to DS_DATA directory!
   # config_file = data_dir + '/' + CONFIGFILE 
   config_file = CONFIGFILE

   try:
      f = open(config_file, 'r')
   except IOError, e:
      print '[tst::read_config]  Open failed: %s\n' % str(e)
      sys.exit(1)

   config_flg     = False
   definition_flg = False

   while True:
      line = f.readline()

      if not line: break

      line = line[:-1]
      line = line.replace('\r','')

      line = line.strip()

      if (line.find("#") != -1): continue

      if (line.find("[Config]") != -1):
         config_flg = True

      elif (line.find("Port=") != -1):
          definition  = line.split("=")

          PORT = int(definition[1].strip())

      elif (line.find("Environment=") != -1):
          definition  = line.split("=")

          ENVIRONMENT = definition[1].strip()

      if (line.find("[Data]") != -1):
         definition_flg = True

      elif (line.find("Description=") != -1):
          definition  = line.split("=")

          (name, source_type, attribute_str) = definition[1].split(":", 2)

          try:
             attributes = eval(attribute_str)
          except:
             attributes = {}

          source = Source(name, ENVIRONMENT, source_type, attributes)

          sources[name] = source

          # print str(source)

   # print "Data definitions loaded..."

   f.close()

#---------------------------------------------------------------------

def get(source_name):
   global hashed
   global indexed
   global index
   global keyed
   global key

   ds = client.Connection(server=HOST, port=PORT, debug=debug_level)

   if (ds == None):
      print("Connection to data-server failed - is data-server process running?\n")
      return 1
   else:
     print("Connected to data-server on port %d" % PORT)

   (type_ref, attributes)  = ds.RegisterType(source_name)

   if attributes['Type'] == 'Hashed':
      hashed   = True
      if not key:
         key      = 'RunNo'

   elif attributes['Type'] == 'Indexed':
      indexed  = True
      if not index:
         index    = 0

   elif attributes['Type'] == 'Keyed':
      keyed    = True
      if not key:
         key      = 'Test'

   if indexed:
      size = attributes['Size']

   pid      = os.getpid()

   print "My PID is %d" % pid

   print "Data type \"%s\" registered (with index) %d ..." % (source_name,  type_ref)
   print "   ... has attributes %s" % (repr(attributes), )
   print

   if keyed:
       sp  = ds.GetNextKeyed(type_ref, key)

   elif hashed:
       sp  = ds.GetHashed(type_ref, key)

       print 'Retrieving hash entry for value "%s"' % hash_key

   elif indexed:
       sp  = ds.GetIndexed(type_ref, index)

   else:
       sp  = ds.GetNext(type_ref)

   if (sp):
      print "Buffer is \"%s\"" % sp

   if sp != None:
      if len(sp) > 0:
         for i in range(len(sp)):
            print "Field %2d: \"%s\"" % (i, sp[i])
      else:
         print "Field: \"%s\"" % None
   else:
     print "Type %d exhausted" % (pid, type_ref)

#---------------------------------------------------------------------

def store(source_name, data):
   global indexed
   global keyed

   ds = client.Connection(port=PORT, debug=debug_level)

   if (ds == None):
      print("Connection to data-server failed - is data-server process running?\n")
      return 1
   else:
     print("Connected to data-server  on port %d\n" % PORT)

   (type_ref, attributes)  = ds.RegisterType(source_name)

   if attributes['Type'] == 'Indexed':
      if not indexed:
         indexed = True
         index   = 0

   elif attributes['Type'] == 'Keyed':
      if not keyed:
         keyed   = True
         key     = 'Test'

   if indexed:
      size = attributes['Size']

   pid      = os.getpid()

   print "My PID is %d" % pid

   print "Data type \"%s\" registered as %d with attributes %s" % (source_name,  type_ref, repr(attributes))

   if keyed:
      ds.StoreKeyedData(type_ref, key, data)
   else:
      ds.StoreCsvData(type_ref, data)

#---------------------------------------------------------------------

def usage():
   print __doc__

#---------------------------------------------------------------------

def main(argv):
   global debug_level
   global term_flg
   global verbose_flg
   global index
   global key
   global store_flg
   global store_data
   global HOST
   global PORT
   global ds_dir
   global data_dir

   no                = 1
   host              = None
   port              = None
   source_name       = None

   store_flg = False

   try:
      opts, args = getopt.getopt(argv, "dD:hH:i:I:k:n:P:s:S:t:Tw:vV?")
   except getopt.error, msg:
      usage()
      return 1

   for o, a in opts:
      if o == '-d':
         debug_level     += 1
      elif o == '-D':
         debug_level      = int(a)
      elif o == '-H':
         host             = a
      elif o == '-i':            # Assuming a numeric offset!
         index            = a
      elif o == '-I':            # Assuming a string index! (i.e. a hash!)
         hashed           = True
         hash_key         = a
      elif o == '-k':
         key              = a
      elif o == '-n':
         no               = int(a)
      elif o == '-P':
         port             = int(a)
      elif o == '-s':
         source_name      = a
      elif o == '-S':
         print "storing..."
         store_flg        = True
         store_data       = a
      elif o == '-t':           # Deprecated term 'table'
         source_name      = a
      elif o == '-T':
         term_flg         = True
      elif o == '-v':
         verbose_flg      = True
      elif o == '-V':
         print "Version: %s" % __version__
         return 0
      elif o == '-w':
         ds_dir           = a
      elif o in ('-h', '-?'):
         usage()
         return 0

   wrk_path  = os.getcwd()
   wrk_dir   = os.path.basename(wrk_path)

   if not ds_dir:
      try:
         ds_dir = os.environ["DSERVER_DIR"]
      except KeyError, e:
         print "No DSERVER_DIR environment variable set!"
         print "Attempting to use local DATA directory..."

         ds_dir = wrk_path

   data_dir = ds_dir + '/DATA/'

   if not os.path.exists(data_dir):
      print "Data directory (%s) does not exist!" % data_dir
      return 1

   os.chdir(data_dir)

   read_config()

   if host:
      HOST = host

   if port:
      PORT = port

   print
   print "Testing data-server at %s:%s" % (HOST, PORT)
   print

   if not sources.has_key(source_name):
      if not source_name:
         print "Specify source..."
      else:
         print "No source, '%s'..." % source_name

      print

      print "Valid sources are:\n"
      print "  Name                   Type"
      print "  ====                   ===="

      for key in sources.keys():
         print "  %s" % sources[key]

      print
      return 0

   if store_flg:                       # STORE
      store(source_name, store_data)
   else:                               # GET
      for i in range(no):
         get(source_name)

#---------------------------------------------------------------------

if __name__ == '__main__' or __name__ == sys.argv[0]:
   sys.exit(main(sys.argv[1:]))

#---------------------------------------------------------------------

"""
Revision History:

     Date     Who   Description
   --------   ---   --------------------------------------------------
   20031014   plh   Initial implementation
   20080716   plh   Merged in 2.1 code variants
   20090130   plh   Read config file to get port and other definitions 
   20090206   plh   Restructured start up logic

Problems to fix:

To Do:

Issues:

"""
