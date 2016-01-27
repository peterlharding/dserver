#!/usr/bin/env python
#
#       Author:  Peter Harding  <plh@performiq.com.au>
#                PerformIQ Pty. Ltd.
#
#                Mobile:  0418 375 085
#
#          Copyright (C) 1994-2016, Peter Harding
#                        All rights reserved
#
#---------------------------------------------------------------------
"""
  Purpose:  Threaded Data Server Implementation

  Usage:

    To start normally:

      $ dserver.py -w /path/to/data/

    To start in debug mode (more detailed logging):

      $ dserver.py -d -w /path/to/data/

    To terminate:

      $ dserver.py -T -w /path/to/data/

      or

      $ dserver.py -T -p <pid>


    To check whether dserver is running:

      $ dserver.py -c -w /path/to/data/

  Notes:

    * Set the DSERVER_DIR environment variable to
      define dserver working (DATA) directory if you
      do not want to explicity specify the path to
      the data.

  Overview:

    Server side: Open a socket on a port, listen for
    a message from a client, and accept a request and
    service it.

    The server spawns a thread to handle each client connection.
    Threads share global memory space with main thread;
    This is more portable than fork which exists on Windows only
    under such POSIX implementations as Cygwin.

    This version has been extended to use the standard Python
    logging module.

    Add the delimiter to the INI file to allow use of alternate
    delimiters in transmitted data - so data with embedded commas
    can be used.
"""
#---------------------------------------------------------------------

import os
import re
import csv
import sys
import time
import getopt
import signal
import thread
import marshal
import logging

#---------------------------------------------------------------------

from socket   import *          # get socket constructor and constants
from datetime import datetime

#---------------------------------------------------------------------

__id__            = "@(#)  dserver.py  [2.2.0]  2011-06-30"
__version__       = re.search(r'.*\[([^\]]*)\].*', __id__).group(1)

check_flg         = False
daemon_flg        = False
silent_flg        = False
terminate_flg     = False
verbose_flg       = False
wait_flg          = False

debug_level       = 0

HOST              = ''             #  Host server - '' means localhost
PORT              = 9578           #  Listen on a non-reserved port number
ENVIRONMENT       = 'SVT'

sockobj           = None
data_dir          = None
client_language   = None
log               = None
sources           = []
attributes        = {}

CONFIGFILE        = "dserver.ini"
LOGFILE           = "dserver.log"
PIDFILE           = "dserver.pid"

INVALID           = 'INVALID'
DELIMITER         = 'delimiter'
TAG_DELIMITER     = 'tag_delimiter'

p_comment         = re.compile('^#')

#=====================================================================

class Group:
   Name     = None
   Idx      = None
   Data     = None

   def __init__(self, name):
      self.Name       = name
      self.Idx        = 0
      self.Data       = []
      self.Comments   = []

   def __str__(self):
      s = "Grp %s  Len %d" % (self.Name, len(self.Data))
      return s

   def append_comments(self, s):
      self.Comments.append(s)

   def append_data(self, s):
      self.Data.append(s)

   def set_idx(self):
      if len(self.Data) > 0:
         self.Idx  = 0
      else:
         self.Idx  = -1

#---------------------------------------------------------------------

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

      # sys.stderr.write("Loading %s\n" % self.Name)
      # sys.stderr.flush()
      # print '[dserver]  Name: "%s"  Type: "%s"  Attributes: "%s"' % (self.Name, self.Type, repr(attributes))

      if not os.path.exists(environment):
         print "[dserver]  Bad environment directory [%s]" % environment
         sys.exit(1)

      tmp_dir = "%s/tmp/" % environment

      if not os.path.exists(tmp_dir):
          os.mkdir(tmp_dir)

      if delimiter:
         self.Delimiter  = delimiter
      elif attributes.has_key(DELIMITER):
         self.Delimiter  = attributes[DELIMITER]
      else:
         self.Delimiter  = ','

      rc = None

      if self.Type == "CSV":
         rc = self.init_csv()

      elif self.Type == "Sequence":
         rc = self.init_sequence()

      elif self.Type == "KeyedSequence":
         if attributes.has_key(TAG_DELIMITER):
            self.tag_delimiter  = attributes[TAG_DELIMITER]
         else:
            self.tag_delimiter  = ':'
         rc = self.init_keyed_sequence()

      elif self.Type == "Hashed":
         if attributes.has_key(TAG_DELIMITER):
            self.tag_delimiter  = attributes[TAG_DELIMITER]
         else:
            self.tag_delimiter  = ':'
         rc = self.init_hashed()

      elif self.Type == "Indexed":
         rc = self.init_indexed()

      elif self.Type == "Keyed":
         rc = self.init_keyed()

      elif self.Type == "Indexer":
         rc = self.init_indexer()

      elif self.Type == "Counter":
         rc = self.init_counter()

      if rc:
         self.Valid = True

      else:
         print "[dserver]  Bad source_type [%s]" % source_type
         sys.exit(1)

      self.Size        = len(self.Data)
      self.Attributes  = {
                            'Type'       : self.Type,
                            'Delimiter'  : self.Delimiter,
                            'Size'       : self.Size
                         }

      try:
         self.ufh = open(self.Used, 'a+')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      try:
         self.sfh = open(self.Stored, 'a+')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

   #------------------------------------------------------------------

   def __str__(self):
      s = "Source: %-22s Type: %-10s" % (self.Name, self.Type)

      if self.Valid:
         s += " * "
         if self.Type == "CSV":
            s += " %9d rows" % len(self.Data)
         elif self.Type == "Sequence":
            s += " Starting value %d" % self.Data[0]
         elif self.Type == "KeyedSequence":
            s += " %9d groups" % len(self.Data)
         elif self.Type == "Hashed":
            s += " %9d rows"   % len(self.Data)
         elif self.Type == "Indexed":
            s += " %9d rows"   % len(self.Data)
         elif self.Type == "Keyed":
            s += " %9d groups" % len(self.Data)
         elif self.Type == "Indexer":
            s += " Starting value %d" % self.Data[0]
         elif self.Type == "Counter":
            s += " Starting value %d" % self.Data[0]
      else:
         s += "   "

      return s

   #------------------------------------------------------------------

   def init_csv(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      self.Data = []

      while True:
         line = f.readline()

         if not line: break

         line = line.strip()

         if p_comment.match(line):
            self.Comments.append(line)
            continue

         self.Data.append(line)

      f.close()

      if len(self.Data) > 0:
         self.Idx = 0
      else:
         self.Idx = None

      if debug_level > 2: 
         INFO("Read in %d CSV rows - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d CSV rows - %s" % (len(self.Data), self.Name)

      #return len(self.Data)
      return True

   #------------------------------------------------------------------

   def init_sequence(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      while True:
         line = f.readline()

         if not line: break

         line = line.strip()

         if p_comment.match(line):
            self.Comments.append(line)
            continue

         elif (len(line) == 0):
            continue

         try:
            no = int(line)
         except:
            no = 0

         self.Data = [no,]

      f.close()

      return True

   #------------------------------------------------------------------

   def init_keyed_sequence(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      groupName  = None
      group      = None

      self.Data  = {}

      while True:
         line = f.readline()

         if not line: break

         line = line.strip()

         if p_comment.match(line):
            self.Comments.append(line)
            continue

         elif (len(line) == 0):
            continue

         else:
            (tag, serial_no) = line.split(self.tag_delimiter)

            tag = tag.strip()

            self.Data[tag] = serial_no

      f.close()

      if debug_level > 2:
         INFO("Read in %d Keyed groups - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d Keyed groups - %s" % (len(self.Data), self.Name)

      return True

   #------------------------------------------------------------------

   def init_keyed(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      groupName  = None
      group      = None

      self.Data  = {}

      while True:
         line = f.readline()

         if not line: break

         line = line.strip()

         if (line.find("[") != -1):
            group_name            = line.replace('[','').replace(']','')
            group                 = Group(group_name)
            self.Data[group_name] = group
            continue

         if p_comment.match(line):
            if group:
               group.append_comment(line)
            else:
               self.Comments.append(line)

         elif (len(line) == 0):
            continue

         else:
            group.append_data(line)

      f.close()

      group_names = self.Data.keys()

      for group_name in group_names:
         group = self.Data[group_name]
         group.set_idx()

      if debug_level > 2:
         INFO("Read in %d Keyed groups - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d Keyed groups - %s" % (len(self.Data), self.Name)

      return True

   #------------------------------------------------------------------

   def init_hashed(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      self.Data = {}

      while True:
         line = f.readline()

         if not line: break

         line = line.strip()

         if p_comment.match(line):
            self.Comments.append(line)
            continue

         elif (len(line) == 0):
            continue

         else:
            (tag, data) = line.split(self.tag_delimiter)

            tag = tag.strip()

            self.Data[tag] = data

      f.close()

      if debug_level > 2:
         INFO("Read in %d hashed rows - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d hashed rows - %s" % (len(self.Data), self.Name)

      return True

   #------------------------------------------------------------------

   def init_indexed(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      self.Data = []

      while True:
         line = f.readline()

         if not line: break

         line = line.strip()

         if p_comment.match(line):
            self.Comments.append(line)
            continue

         elif (len(line) == 0):
            continue

         else:
            self.Data.append(line)

      f.close()

      if debug_level > 2:
         INFO("Read in %d indexed rows - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d indexed rows - %s" % (len(self.Data), self.Name)

      return len(self.Data)

   #------------------------------------------------------------------

   def init_indexer(self):
      self.Data = [0,]

      return True

   #------------------------------------------------------------------

   def init_counter(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         sys.exit(1)

      while True:
         line = f.readline()

         if not line: break

         line = line.strip()

         if p_comment.match(line):
            self.Comments.append(line)
            continue

         elif (len(line) == 0):
            continue

         try:
            no = int(line)
         except:
            no = 0

         self.Data = [no,]

      f.close()

      return True

   #------------------------------------------------------------------

   def flush(self):
      if not self.Valid:
         return

      ts = datetime.now().strftime('%Y%m%d%H%M%S')

      self.BackupCmd  = "cp %s/%s.dat %s/tmp/%s_%s.bak" % (self.Environment, self.Name, self.Environment, ts, self.Name)

      print "Flushing %s" % self.Name

      if self.Type == "CSV":
         self.flush_csv()
      elif self.Type == "Sequence":
         self.flush_sequence()
      elif self.Type == "KeyedSequence":
         self.flush_keyed_sequence()
      elif self.Type == "Keyed":
         self.flush_keyed()
      elif self.Type == "Hashed":
         self.flush_hashed()
      elif self.Type == "Indexed":
         self.flush_indexed()
      elif self.Type == "Indexer":
         pass  # DO nothing!
      elif self.Type == "Counter":
         self.flush_counter()

   #------------------------------------------------------------------

   def flush_csv(self):
      os.system(self.BackupCmd)

      try:
         f = open(self.File, 'wb')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         return 0

      for line in  self.Comments:
         f.write("%s\n" % line)

      l = len(self.Data)
      if l > 0:
         i = self.Idx
         while i < len(self.Data):
            f.write("%s\n" % self.Data[i])
            i += 1

      f.close()

   #------------------------------------------------------------------

   def flush_sequence(self):
      os.system(self.BackupCmd)

      try:
         f = open(self.File, 'wb')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         return 0

      for line in  self.Comments:
         f.write("%s\n" % line)

      f.write("%d\n" % self.Data[0])

      f.close()

   #------------------------------------------------------------------

   def flush_keyed_sequence(self):
      os.system(self.BackupCmd)

      try:
         f = open(self.File, 'wb')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         return 0

      group_keys = self.Data.keys()

      group_keys.sort()

      for line in  self.Comments:
         f.write("%s\n" % line)

      for key in group_keys:
         f.write("%s%s%s\n" % (key, self.tag_delimiter, self.Data[key]))

      f.close()

   #------------------------------------------------------------------

   def flush_keyed(self):
      os.system(self.BackupCmd)

      try:
         f = open(self.File, 'wb')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         return 0

      group_keys = self.Data.keys()

      group_keys.sort()

      for line in  self.Comments:
         f.write("%s\n" % line)

      for key in group_keys:
         f.write("[%s]\n" % key)

         group = self.Data[key]

         for line in  group.Comments:
            f.write("%s\n" % line)

         i = group.Idx

         while i < len(group.Data):
            f.write("%s\n" % group.Data[i])
            i += 1

         f.write("\n")

      f.close()

   #------------------------------------------------------------------

   def flush_hashed(self):
      pass

   #------------------------------------------------------------------

   def flush_indexed(self):
      pass

   #------------------------------------------------------------------

   def flush_counter(self):
      try:
         f = open(self.File, 'wb')
      except IOError, e:
         sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
         return 0

      for line in  self.Comments:
         f.write("%s\n" % line)

      i = int(self.Data[0]) + 1

      f.write("%d\n" % i)

      f.close()

#=====================================================================

def INFO(msg):
   if log: log.info(' ' + msg)
   if verbose_flg: print "[dserver]  %s" % msg

#---------------------------------------------------------------------

def ERROR(msg):
   if log: log.error(msg)
   sys.stderr.write('[dserver]  %s\n' % msg)

#---------------------------------------------------------------------

def WARNING(msg):
   if log: log.warning('*****' + msg + '*****')
   if verbose_flg: print "[dserver]  %s" % msg

#=====================================================================

def read_config():
   global PORT, ENVIRONMENT

   config_file = data_dir + '/' + CONFIGFILE

   try:
      f = open(config_file, 'r')
   except IOError, e:
      msg = '[dserver::read_config]  Open failed: %s\n' % str(e)
      ERROR(msg)
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

          sources.append(source)

          INFO(str(source))

          print "Loaded %s" % str(source)

   print "\nData Loaded...\n"

   f.close()

#---------------------------------------------------------------------

def get_source_index(name):
   for i in range(len(sources)):
      if (sources[i].Name == name):
         return i

   return -1

#---------------------------------------------------------------------

def process(s):
   global client_language

   msg = s.split("|")
   l   = len(msg)

   if debug_level > 1:  INFO("[dserver::process] len %d  msg %s" % (l, msg))

   ts    = datetime.now().strftime('%Y%m%d%H%M%S')
   reply = "None"

   if (msg[0] == "INIT"):
      client_language = msg[1]

      if client_language == 'Python':
         reply = "%s" % marshal.dumps(attributes)
      else:  # client_language == 'C'
         reply = "0"

   elif (msg[0] == "REG"):
      name = msg[1].replace('\n','').replace('\r','')
      idx  = get_source_index(name)
      if debug_level > 0:  INFO("[dserver::process]  REG '%s' -> %d" % (name, idx))

      if client_language == 'Python':
         reply = "%d|%s" % (idx, marshal.dumps(sources[idx].Attributes))
      else:  # client_language == 'C'
         reply = "%d" % idx

   elif (msg[0] == "REGK"):
      if (len(msg) != 3):
         ERROR("[dserver::process]  REGK -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"
      else:
         reply = "0"

   elif (msg[0] == "REGI"):
      if (len(msg) != 2):
         ERROR("[dserver::process]  REGI -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"
      else:
         reply = "0"

   elif (msg[0] == "GETN"):
      if (len(msg) == 2):
         hdl  = int(msg[1])

         try:
            source = sources[hdl]
         except:
            source = None

         if source != None:
            if source.Type == 'CSV':
               if ((source.Idx != None) and (source.Idx < len(source.Data))):
                  reply  = source.Data[source.Idx]
                  source.Idx += 1
               else:
                  reply = "*Exhausted*"
            elif source.Type == "Sequence":
               reply = "%d" % source.Data[0]
               source.Data[0] += 1
            elif source.Type == "Indexer":
               reply = "%d" % source.Data[0]
               source.Data[0] += 1
            elif source.Type == "Counter":
               reply = "%d" % source.Data[0]
            else:
               reply = "*UNKNOWN*SOURCE*TYPE*"
         else:
            reply = "*BAD*SOURCE*INDEX*"

         source.ufh.write("%s - %s\n" % (ts, reply))
         source.ufh.flush()
      else:
         ERROR("[dserver::process]  GETN -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"

      if debug_level > 2:  INFO("[dserver::process]  GETN -> %s" % reply)

   elif (msg[0] == "GETKS"):
      if (len(msg) == 3):
         hdl  = int(msg[1])
         grp  = msg[2]

         try:
            source = sources[hdl]
         except:
            source = None

         if source != None:
            try:
               g = source.Data[grp]
            except:
               g = None
            if g != None:
               reply  = g.Data[0]
               g.Data[0] += 1
               g.Idx += 1
            else:
               reply = "*INVALID*GROUP*"

         else:
            reply = "*BAD*SOURCE*INDEX*"

         source.ufh.write("%s - %s::%s\n" % (ts, grp, reply))
         source.ufh.flush()
      else:
         ERROR("[dserver::process]  GETKS -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"

      if debug_level > 2:  INFO("[dserver::process]  GETKS %s -> %s" % (grp, reply))

   elif (msg[0] == "GETK"):
      if (len(msg) == 3):
         hdl  = int(msg[1])
         grp  = msg[2]

         try:
            source = sources[hdl]
         except:
            source = None

         if source != None:
            try:
               g = source.Data[grp]
            except:
               g = None

            if g != None:
               if (g.Idx < len(g.Data)):
                  reply  = g.Data[g.Idx]
                  g.Idx += 1
               else:
                  reply = "*GROUP*EXHAUSTED*"
            else:
               reply = "*INVALID*GROUP*"

         else:
            reply = "*BAD*SOURCE*INDEX*"

         source.ufh.write("%s - %s::%s\n" % (ts, grp, reply))
         source.ufh.flush()
      else:
         ERROR("[dserver::process]  GETK -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"

      if debug_level > 2:  INFO("[dserver::process]  GETK %s -> %s" % (grp, reply))

   elif (msg[0] == "GETH"):
      if (len(msg) == 3):
         hdl  = int(msg[1])
         key  = msg[2]

         try:
            source = sources[hdl]
         except:
            source = None

         if source != None:
            try:
               reply = source.Data[key]
            except:
               reply = "*UNDEFINED*HASH*"

         else:
            reply = "*BAD*SOURCE*INDEX*"

         source.ufh.write("%s - %s::%s\n" % (ts, key, reply))
         source.ufh.flush()
      else:
         ERROR("[dserver::process]  GETH -> Bad Message", msg)
         reply = "*BAD*MESSAGE*"

      if debug_level > 2:  INFO("[dserver::process]  GETH %s -> %s" % (key, reply))

   elif (msg[0] == "GETI"):
      if (len(msg) == 3):
         hdl    = int(msg[1])

         try:
            idx = int(msg[2])
         except:
            idx = None
            ERROR("[dserver::process]  GETI -> Non integer index - [%s]" % msg[2])

         try:
            source = sources[hdl]
         except:
            source = None

         if source != None:
            if ((idx >= 0) and (idx < len(source.Data))):
               try:
                  reply = source.Data[idx]
               except:
                  reply = "*INDEX*OUT*OF*RANGE*"
            else:
               reply = "*INVALID*INDEX*"
         else:
            reply = "*BAD*SOURCE*INDEX*"

         source.ufh.write("%s - %s::%s\n" % (ts, idx, reply))
         source.ufh.flush()
      else:
         ERROR("[dserver::process]  GETI -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"

      if debug_level > 2:  INFO("[dserver::process]  GETI %s -> %s" % (idx, reply))

   elif (msg[0] == "STOC"):
      if (len(msg) == 3):
         hdl   = int(msg[1])
         data  = msg[2]
         reply = "0"

         try:
            source = sources[hdl]
         except:
            source = None

         if source != None:
            source.Data.append(data)
            if source.Idx == None:
               source.Idx = 0
            source.sfh.write("%s - %s\n" % (ts, data))
            source.sfh.flush()
            if debug_level > 1: INFO("STOC %s" % data)
            reply = "1"
         else:
            reply = "*BAD*SOURCE*INDEX*"
      else:
         ERROR("[dserver::process]  STOC -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"

      if debug_level > 2:  INFO("[dserver::process]  STOC %s -> %s" % (data, reply))

   elif (msg[0] == "STOK"):
      if (len(msg) == 4):
         hdl  = int(msg[1])
         grp  = msg[2]
         data = msg[3]

         reply = "0"

         try:
            source = sources[hdl]
         except:
            source = None

         if source != None:
            if source.Data.has_key(grp):
               g                = source.Data[grp]
            else:
               g                = Group(grp)
               source.Data[grp] = g
            if g != None:
               g.Data.append(data)
               if debug_level > 1: INFO("STOK %s %s" % (grp, data))
               source.sfh.write("%s - %s::%s\n" % (ts, grp, data))
               source.sfh.flush()
            reply = "1"
         else:
            reply = "*BAD*SOURCE*INDEX*"
      else:
         ERROR("[dserver::process]  STOK -> Bad Message '%s'" % str(msg))
         reply = "*BAD*MESSAGE*"

      if debug_level > 2:  INFO("[dserver::process]  STOK %s %s -> %s" % (grp, data, reply))

   return reply

#---------------------------------------------------------------------

def sig_term(signum, frame):
   "SIGTERM handler"

   shutdown()

#---------------------------------------------------------------------

def shutdown():
   INFO("Server shutdown at %s" % datetime.now())

   print "\n"

   for i in range(len(sources)):
      sources[i].flush()

   print "*SHUTDOWN*"

   try:
      os.unlink(PIDFILE)
   except IOError, e:
      ERROR('Unlink failed: %s' % str(e))
      sys.exit(1)

   sys.exit(0)

#---------------------------------------------------------------------

def check_running():
   try:
      pfp = open(PIDFILE, 'r')
   except IOError, (errno, strerror):
      pfp = None
      # ERROR("I/O error(%s): %s" % (errno, strerror))
   except:
      ERROR("Unexpected error: %s" % sys.exc_info()[0])
      raise

   if pfp:
      line = pfp.readline()
      line = line.strip()

      dserver_pid   = int(line)

      if debug_level > 0:
         print "Found PID file with PID (%d)", dserver_pid

      noProcess    = False

      try:
         os.kill(dserver_pid, 0)
      except OSError, e:
         if e.errno == 3:
            noProcess = True
         else:
            ERROR("kill() failed: %s" % str(e))
            sys.exit(0)

      if noProcess:
         if debug_level > 0:
            print "PID file is stale!"
         INFO("[dserver]  Stale dserver pid file!")
         pfp.close()
         os.unlink(PIDFILE)

         return None
      else:
         pfp.close()
         return dserver_pid

      return dserver_pid
   else:
      return None

#---------------------------------------------------------------------

def create_pidfile():
   pid = os.getpid()

   try:
      pfp = open(PIDFILE, 'w')
   except IOError, e:
      ERROR("Open failed: %s" % str(e))
      sys.exit(0)

   pfp.write("%d" % pid)

   pfp.close()

   INFO("Running server with PID -> %d" % pid)

   return pid

#---------------------------------------------------------------------

def become_daemon():
   pid = os.fork()

   if pid == 0:                                             # In child
      pid = create_pidfile()
      time.sleep(1)
   elif pid == -1:                                # Should not happen!
      ERROR("fork() failed!")
      time.sleep(1)
      sys.exit(0)
   else:                                                   # In Parent
      time.sleep(1)
      sys.exit(0)

   time.sleep(2)

   os.setsid()

   return pid

#---------------------------------------------------------------------

def init_logging():
   global log

   log  = logging.getLogger('dserver')
   hdlr = logging.FileHandler(LOGFILE)
   fmtr = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

   hdlr.setFormatter(fmtr)
   log.addHandler(hdlr)
   log.setLevel(logging.INFO)

   INFO("Server startup at %s" % datetime.now())

#---------------------------------------------------------------------

def init_server():
   pid = check_running()

   if pid:
      print "[dserver]  Server already running! (pid = %d)" % pid
      sys.exit(0)

   if daemon_flg:
      pid = become_daemon()
   else:
      pid = create_pidfile()

   INFO("Started processing")

   if (not silent_flg):
      INFO("Server PID is %d" % pid)

   setup_connection()

   print "[dserver]  Listening on port %s - Data from %s" % (PORT, os.getcwd())

   dispatcher()

#---------------------------------------------------------------------

def terminate(pid=None):
   if pid:
      dserver_pid = pid
   else:
      dserver_pid = check_running()

   if dserver_pid:
      print "Attempting to terminate server with PID: %d" % dserver_pid

      try:
         os.kill(dserver_pid, signal.SIGTERM)
      except OSError, e:
         print "[terminate]  kill() failed:  %s" % str(e)

      if (wait_flg):
         while True:
            try:
               kill(dserver_pid, 0)
            except OSError, e:
               if e.errno == 3:
                  break
               else:
                  print "[terminate]  kill() failed:  %s" % str(e)
                  sys.exit(0)

            time.sleep(1)
   else:
      print "Data server not running!"

   return 0

#---------------------------------------------------------------------

def check():
   pid = check_running()

   if pid:
      print "[dserver]  Server already running! (pid = %d)" % pid
      sys.exit(0)
   else:
      print "[dserver]  Server not running"

#==== Socket Server ==================================================

def setup_connection():
   global sockobj

   sockobj = socket(AF_INET, SOCK_STREAM)  # make a TCP socket object
   sockobj.bind((HOST, PORT))              # bind it to server port number
   sockobj.listen(10)                      # allow upto 10 pending connects

#---------------------------------------------------------------------

def handle_client(connection):             # in spawned thread: reply
   while True:                             # read, write a client socket
      try:
         request = connection.recv(1024)
      except:
         break

      if debug_level > 0: INFO('[dserver]  Request -> "%s"' % request)

      if not request: break

      reply = process(request)

      if debug_level > 0: INFO('[dserver]  Reply   -> "%s..."' % reply[0:30])

      connection.send(reply)

   connection.close()

#---------------------------------------------------------------------

def dispatcher():
   while True:
      # Wait for next connection,
      connection, address = sockobj.accept()

      INFO('Host (%s) - Connected at %s' % (address[0], datetime.now()))

      thread.start_new(handle_client, (connection,))

#=====================================================================

def main():
   global check_flg
   global daemon_flg
   global terminate_flg
   global verbose_flg
   global wait_flg
   global debug_level
   global data_dir

   data_dir   = None
   pid        = None

   try:
      opts, args = getopt.getopt(sys.argv[1:], "cdDp:sTvVw:W?")
   except getopt.error, msg:
      print __doc__
      return 1

   for o, a in opts:
      if o == '-d':
         debug_level   += 1
      elif o == '-c':
         check_flg      = True
      elif o == '-D':
         daemon_flg     = True
      elif o == '-p':
         pid            = int(a)
      elif o == '-s':
         tsilent_flg    = True
      elif o == '-T':
         terminate_flg  = True
      elif o == '-v':
         verbose_flg    = True
      elif o == '-V':
         print "[dserver]  Version: %s" % __version__
         return 1
      elif o == '-w':
         data_dir       = a
      elif o == '-W':
         wait_flg       = True
      elif o == '-?':
         print __doc__
         return 1

   print "\n"

   wrk_path  = os.getcwd()
   wrk_dir   = os.path.basename(wrk_path)

   if not data_dir:
      try:
         data_dir = os.environ["DSERVER_DIR"]
      except KeyError, e:
         print "No DSERVER_DIR environment variable set!"
         print "Attempting to use local DATA directory..."

         data_dir = wrk_path + '/DATA/'

   if not os.path.exists(data_dir):
      print "Data directory (%s) does not exist!" % data_dir
      return 1

   os.chdir(data_dir)

   if check_flg:
      check()
      return 0

   if terminate_flg:
      terminate(pid)
      return 0

   if (debug_level > 0): print "[dserver]  Debugging level set to %d\n" % debug_level

   signal.signal(signal.SIGTERM, sig_term)

   init_logging()

   read_config()

   init_server()

   return 0

#---------------------------------------------------------------------

if __name__ == '__main__' or __name__ == sys.argv[0]:
   try:
      sys.exit(main())
   except KeyboardInterrupt, e:
      print "[dserver]  Interrupted!"
      shutdown()

#---------------------------------------------------------------------

"""
Revision History:

     Date     Who   Description
   --------   ---   --------------------------------------------------
   20031014   plh   Initial implementation
   20080609   plh   Added exception handling to read_indexed()
   20080609   plh   Reformatted exception strings
   20080610   plh   Reformatted log text for load
   20080610   plh   Reviewed __id__ and __version__ strings
   20100616   plh   Convert Sequence data to a list
   20110510   plh   Add tmp sub-dir back into environment specific data
   20110603   plh   Implemented Indexer method - reset to 0 on each restart
   20110603   plh   Implemented ReadCounter method
   20110603   plh   Renamed read_* methods to init_*

Problems to fix:

To Do:

Issues:

"""

