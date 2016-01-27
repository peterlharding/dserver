#!/usr/bin/env python
#
#       Author:  Peter Harding  <plh@pha.com.au>
#                PerformIQ Pty. Ltd.
#                Level 6, 179 Queen Street,
#                MELBOURNE, VIC, 3000
# 
#                Phone:   03 9641 2222
#                Fax:     03 9641 2200
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

    # recover.py -t <table> 

      The '-t <table>' option is used to specify the name
      of the table to recover

"""
#---------------------------------------------------------------------

import os
import re
import sys
import getopt

import dserver

#---------------------------------------------------------------------

__id__            = "@(#) [1.0.0] recover.py 2011-07-20"
__version__       = re.search(r'.*\[([^\]]*)\].*', __id__).group(1)

#---------------------------------------------------------------------

HOST              = 'dserver'
PORT              = 9578
environment       = 'SVT'

debug_level       = 0
verbose_flg       = False

ds_dir            = None
data_dir          = None

CONFIG_FILE       = "dserver.ini"

sources           = {}

p_crlf            = re.compile(r'[\r\n]*')
p_comment         = re.compile('^#')

#=====================================================================

class Group:
   Name     = None
   Idx      = None
   Data     = None
   Comments = None

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

class BarcodeGroup(Group):
   Prefix     = 'EE'
   Range      = 99
   Country    = 'AU'

   def __init__(self, name):
      (prefix, range, country) = name.split('-')

      self.Name       = name
      self.Prefix     = prefix
      self.Range      = int(range)
      self.Country    = country
      self.Serial     = None

   def __str__(self):
      s = "Grp %s  Serial %d" % (self.Name, self.Serial)
      return s

#---------------------------------------------------------------------

class Source:
   Environment  = 'SVT'
   Count        = 0
   Size         = 0
   Valid        = False
   Name         = None
   Type         = None
   Idx          = None
   Data         = None

   def __init__(self, name, environment, source_type, attributes={}, delimiter=None):
      self.Name        = name
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
      elif attributes.has_key('Delimiter'):
         self.Delimiter  = attributes['Delimiter']
      else:
         self.Delimiter  = ','

      if source_type != 'Indexer' and not os.path.exists(self.File):
         print "[dserver]  File [%s] - Bad source_type [%s]" % (name, source_type)

      self.Attributes              = attributes
      self.Attributes['Type']      = self.Type,
      self.Attributes['Delimiter'] = self.Delimiter,

   #------------------------------------------------------------------

   def __str__(self):
      s = "Source: %-22s Type: %-15s" % (self.Name, self.Type)

      if self.Valid:
         s += " * "
         if self.Type == "CSV":
            s += " %9d rows" % len(self.Data)
         elif self.Type == "Sequence":
            s += " Starting value:  %d" % self.Data
         elif self.Type == "KeyedSequence":
            s += " %9d groups" % len(self.Data)
         elif self.Type == "Hashed":
            s += " %9d rows"   % len(self.Data)
         elif self.Type == "Indexed":
            s += " %9d rows"   % len(self.Data)
         elif self.Type == "Keyed":
            s += " %9d groups" % len(self.Data)
         elif self.Type == "Indexer":
            s += " Starting value:  %d" % self.Data
         elif self.Type == "Counter":
            s += " Value:  %d" % self.Data
         elif self.Type == "Barcodes":
            s += " %9d groups" % len(self.Data)
      else:
         s += "   "

      return s

   #------------------------------------------------------------------

   def init(self, rw=True):
      rc = False

      if self.Type == "CSV":
         rc = self.init_csv()

      elif self.Type == "Sequence":
         rc = self.init_sequence()

      elif self.Type == "KeyedSequence":
         if self.Attributes.has_key('TagDelimiter'):
            self.TagDelimiter  = attributes['TagDelimiter']
         else:
            self.TagDelimiter  = ':'
         rc = self.init_keyed_sequence()

      elif self.Type == "Hashed":
         if self.Attributes.has_key('TagDelimiter'):
            self.TagDelimiter  = attributes['TagDelimiter']
         else:
            self.TagDelimiter  = ':'
         rc = self.init_hashed()

      elif self.Type == "Indexed":
         rc = self.init_indexed()

      elif self.Type == "Keyed":
         rc = self.init_keyed()

      elif self.Type == "Indexer":
         if self.Attributes.has_key('start'):
            self.Data = self.Attributes['start']
         else:
            self.Data = 1
         rc = True

      elif self.Type == "Counter":
         rc = self.init_counter()

      elif self.Type == "Barcodes":
         if self.Attributes.has_key('TagDelimiter'):
            self.TagDelimiter  = self.Attributes['TagDelimiter']
         else:
            self.TagDelimiter  = ':'
         rc = self.init_barcodes()

      if rc:
         self.Valid = True
      else:
         print "[init]  Bad source type [%s]" % source_type
         sys.exit(1)

      if rw == True:
         mode = 'a+'
      else:
         mode = 'r'

      try:
         self.f_used = open(self.Used, mode)
      except IOError, e:
         sys.stderr.write('[init]  Open failed: %s\n' % str(e))
         sys.exit(1)

      try:
         self.f_stored = open(self.Stored, mode)
      except IOError, e:
         sys.stderr.write('[init]  Open failed: %s\n' % str(e))
         sys.exit(1)

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
               group.Comments.append(line)
            else:
               self.Comments.append(line)

         elif (len(line) == 0):
            continue

         else:
            group.Data.append(line)

      f.close()

      if debug_level > 2:
         INFO("Read in %d Keyed groups - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d Keyed groups - %s" % (len(self.Data), self.Name)

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
            (tag, serial_no) = line.split(self.TagDelimiter)

            tag = tag.strip()

            self.Data[tag] = int(serial_no)

      f.close()

      if debug_level > 2:
         INFO("Read in %d Keyed groups - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d Keyed groups - %s" % (len(self.Data), self.Name)

      return True

   #------------------------------------------------------------------

   def init_barcodes(self):
      try:
         f = open(self.File, 'r')
      except IOError, e:
         sys.stderr.write('[init_barcode]  Open failed: %s\n' % str(e))
         sys.exit(1)

      groupName  = None
      group      = None

      self.Data  = {}

      while True:
         line = f.readline()

         if not line: break

         line = p_crlf.sub('', line)

         if p_comment.match(line):
            self.Comments.append(line)
            continue

         elif (len(line) == 0):
            continue

         else:
            (barcode_type, serial_no) = line.split(self.TagDelimiter)

            barcode_type = barcode_type.strip()

            barcode_specification        = BarcodeGroup(barcode_type)
            barcode_specification.Serial = int(serial_no)
            self.Data[barcode_type]      = barcode_specification

      f.close()

      if debug_level > 2:
         INFO("Read in %d barcode groups - %s" % (len(self.Data), self.Name))
         if verbose_flg:  print "Read in %d barcode groups - %s" % (len(self.Data), self.Name)

      return True

   #------------------------------------------------------------------

   def recover_keyed(self):
      """
      20110719175608 - AUSYDBTHBKKB::EE160567961AU,dbc3c1ae-8ee1-4ad5-8fd7-4f274cd60303,2011-07-19 17:56:07
      20110719175617 - AUSYDBUSHNLA::EE160567975AU,ee78cd91-9707-4257-86ef-5d0c129d58ff,2011-07-19 17:56:16
      20110719175617 - AUSYDBUSHNLA::EE160567989AU,5a4ad8f2-56ba-4ce1-a372-1ca92806848c,2011-07-19 17:56:16
      """

      p_keyed = re.compile(r'[0-9]* - ([^:]*)::(.*)$')

      group_tags = self.Data.keys()

      group_tags.sort()

      print
      print "Data:"

      for group_tag in group_tags:
         group              = self.Data[group_tag]
         group.orig_no_rows = len(group.Data)

         print "%s [%d]:" % (group_tag, group.orig_no_rows)

         group.last_data  = group.Data[group.orig_no_rows-1]
         group.Used       = []
         group.Stored     = []

      # Recover the stored items...

      cnt = 0

      while True:
         line = self.f_stored.readline()

         if not line: break

         line = p_crlf.sub('', line)

         if len(line) == 0:  continue

         cnt += 1

         m = p_keyed.match(line)

         if m:
            group_tag    = m.group(1)
            data         = m.group(2)
            group = self.Data[group_tag]
            group.Stored.append(data)

      print
      print "Stored:"

      for group_tag in group_tags:
         group = self.Data[group_tag]
         no_rows = len(group.Stored)
         print "%s [%d]:" % (group_tag, no_rows)

      print
      print "Recovering stored data..."

      for group_tag in group_tags:
         group = self.Data[group_tag]

         no_rows = len(group.Stored)

         new_data_start_idx = no_rows
         idx                = no_rows - 1

         while idx >= 0:
            if group.Stored[idx] != group.last_data:  # Must be a new one!
               idx -= 1
               continue
            else:  # got back to an existing one
               new_data_start_idx = idx + 1
               break

         delta = no_rows - new_data_start_idx

         if delta > 0:
            ch = '*'
         else:
            ch = ' '

         if new_data_start_idx < no_rows:
            idx = new_data_start_idx
            while idx < no_rows:
               group.Data.append(group.Stored[idx])
               idx += 1

         print "%-10s -> %5d [%05d] %5d %c %5d  %5d %5d" % (group_tag, new_data_start_idx,
             no_rows, delta, ch, group.orig_no_rows, len(group.Data),
             len(group.Data) - group.orig_no_rows)

      print

      # Now get rid of the used ones...

      cnt = 0

      while True:
         line = self.f_used.readline()

         if not line: break

         line = p_crlf.sub('', line)

         if len(line) == 0:  continue

         cnt += 1

         m = p_keyed.match(line)

         if m:
            group_tag    = m.group(1)
            data         = m.group(2)

            group = self.Data[group_tag]

            if data != '*Exhausted*':
               barcode, rest = data.split(',', 1)
               group.Used.append(barcode)

      print
      print "Now analyse Used data..."
      print

      for group_tag in group_tags:
         group = self.Data[group_tag]

         print ">>>%s<<<" % group_tag

         # Gather the barcodes

         data = {}

         for idx in range(len(group.Data)-1):
            try:
               ref_data, rest = group.Data[idx].split(',', 1)
            except:
               ref_data       = group.Data[idx]

            data[ref_data] = idx

         for u in group.Used:
            if data.has_key(u):  # So pop it off the beginning
               print "%s:  %d" % (group_tag, data[u])
               group.Data.pop(0)
            else:  # Gone already!
               continue

         print

      print

   #------------------------------------------------------------------

   def recover_keyed_sequence(self):
      p_keyed = re.compile(r'[0-9]* - ([^:]*)::(.*)$')

      group_tags = self.Data.keys()

      group_tags.sort()

      print
      print "Data:"

      for group_tag in group_tags:
         serial_no              = self.Data[group_tag]

         print "%s [%d]:" % (group_tag, serial_no)

         used       = {}

      # Recover the stored items...

      cnt = 0

      while True:
         line = self.f_used.readline()

         if not line: break

         line = p_crlf.sub('', line)

         if len(line) == 0:  continue

         cnt += 1

         m = p_keyed.match(line)

         if m:
            group_tag    = m.group(1)
            data         = m.group(2)

            # print "%s: %s" % (group_tag, data)

            if data == '*NO*VALID*KEY*':
               continue
            elif data == '*BAD*GROUP*':
               continue

            serial_no    = int(data)

            if self.Data.has_key(group_tag):
               value = self.Data[group_tag]
               if serial_no > value:
                  self.Data[group_tag] = value

      print

      for group_tag in group_tags:
         serial_no              = self.Data[group_tag]

         print "%s [%d]:" % (group_tag, serial_no)

      print

   #------------------------------------------------------------------

   def recover_barcodes(self):
      """
        20110717124124 - EE-16-AU::EE160000218AU
      """

      # p_line = re.compile(r'[0-9]* - ([^:]*)::....(.*)...$')
      p_line = re.compile(r'[0-9]* - ([^:]*)::([0-9]*)$')

      cnt = 0

      barcode_types = self.Data.keys()

      for barcode_type in barcode_types:
         self.Data[barcode_type].RecoveredSerial = 0

      while True:
         line = self.f_used.readline()

         if not line: break

         line = p_crlf.sub('', line)

         if len(line) == 0:  continue

         print line

         cnt += 1

         m = p_line.match(line)


         if m:
            barcode_type = m.group(1)
            serial       = int(m.group(2))

            barcode = self.Data[barcode_type]

            if serial > barcode.RecoveredSerial:
               barcode.RecoveredSerial = serial 

            print "%s >> %d" % (barcode_type, serial)

         # if cnt > 100:  break


   #------------------------------------------------------------------

   def list(self):
      if self.Type == "CSV":
         self.list_csv()
      elif self.Type == "Keyed":
         self.list_keyed()
      elif self.Type == "Barcodes":
         self.list_barcodes()

   #------------------------------------------------------------------

   def list_keyed(self):
      group_tags = self.Data.keys()

      group_tags.sort()

      for group_tag in group_tags:
         group = self.Data[group_tag]

         no_rows = len(group.Data)
         first_row = group.Data[0]
         last_row  = group.Data[no_rows-1]
         print "%s [%d]:" % (group_tag, no_rows)
         print "  %s" % first_row
         print "  ..."
         print "  %s" % last_row
         print

   #------------------------------------------------------------------

   def list_keyed_sequence(self):
      group_tags = self.Data.keys()

      group_tags.sort()

      for group_tag in group_tags:
         serial_no = self.Data[group_tag]
         print "%s: %d" % (group_tag, serial_no)

   #------------------------------------------------------------------

   def list_barcodes(self):
      keys = self.Data.keys()

      keys.sort()

      for key in keys:
         print("%s%s%d" % (key, self.TagDelimiter, self.Data[key].Serial))

   #------------------------------------------------------------------

   def list_recovered_barcodes(self):
      keys = self.Data.keys()

      keys.sort()

      for key in keys:
         print("%s%s%d" % (key, self.TagDelimiter, self.Data[key].RecoveredSerial+1))

   #------------------------------------------------------------------

   def flush_keyed(self, recover=False):
      if recover:
         file = '%s/%s.rec' % (Source.Environment, self.Name)
      else:
         file = self.File
         os.system(self.BackupCmd)

      try:
         f = open(file, 'wb')
      except IOError, e:
         sys.stderr.write('[flush_keyed]  Open failed: %s\n' % str(e))
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

   def flush_keyed_sequence(self, recover=False):
      if recover:
         file = '%s/%s.rec' % (Source.Environment, self.Name)
      else:
         file = self.File
         os.system(self.BackupCmd)

      try:
         f = open(file, 'wb')
      except IOError, e:
         sys.stderr.write('[flush_keyed_sequence]  Open failed: %s\n' % str(e))
         return 0

      group_keys = self.Data.keys()

      group_keys.sort()

      for line in  self.Comments:
         f.write("%s\n" % line)

      for key in group_keys:
         f.write("%s:%d\n" % (key, self.Data[key]))

      f.close()

   #------------------------------------------------------------------

   def flush_barcodes(self, recover=False):
      if recover:
         file = '%s/%s.rec' % (Source.Environment, self.Name)
      else:
         file = self.File
         os.system(self.BackupCmd)

      try:
         f = open(file, 'wb')
      except IOError, e:
         sys.stderr.write('[flush_barcodes]  Open failed: %s\n' % str(e))
         return 0

      keys = self.Data.keys()

      keys.sort()

      for line in  self.Comments:
         f.write("%s\n" % line)

      for key in keys:
         f.write("%s%s%d\n" % (key, self.TagDelimiter, self.Data[key].RecoveredSerial+1))

      f.close()

#=====================================================================

def read_config():
   global PORT, environment

   # Have cd'd to DS_DATA directory!
   # config_file = data_dir + '/' + CONFIG_FILE 
   config_file = CONFIG_FILE

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

      line = p_crlf.sub('', line)

      if (line.find("#") != -1): continue

      if (line.find("[Config]") != -1):
         config_flg = True

      elif (line.find("Port=") != -1):
          definition  = line.split("=")

          PORT = int(definition[1].strip())

      elif (line.find("Environment=") != -1):
          definition  = line.split("=")

          environment = definition[1].strip()

      if (line.find("[Data]") != -1):
         definition_flg = True

      elif (line.find("Description=") != -1):
          definition  = line.split("=")

          (name, source_type, attribute_str) = definition[1].split(":", 2)

          try:
             attributes = eval(attribute_str)
          except:
             attributes = {}

          source = Source(name, environment, source_type, attributes)

          sources[name] = source

          # print str(source)

   # print "Data definitions loaded..."

   Source.Environment = environment

   f.close()

#---------------------------------------------------------------------

def recover_serial(source):
   print "Source - %s (%s)" % (source.Name, source.Type)

#---------------------------------------------------------------------

def recover_serial(source):
   print "Source - %s (%s)" % (source.Name, source.Type)

#---------------------------------------------------------------------

def recover_csv(source):
   print "Source - %s (%s)" % (source.Name, source.Type)

#---------------------------------------------------------------------

def recover_keyed(source):
   print "Source - %s (%s)" % (source.Name, source.Type)

   source.init(rw=False)

   print "===== Keyed Data ===================="

   source.list_keyed()

   source.recover_keyed()

   print "===== Recovered Keyed Data =========="

   source.list_keyed()

   source.flush_keyed(recover=True)

#---------------------------------------------------------------------

def recover_keyed_sequence(source):
   print "Source - %s (%s)" % (source.Name, source.Type)

   source.init(rw=False)

   print "===== Keyed Sequence Data ==========="

   source.list_keyed_sequence()

   source.recover_keyed_sequence()

   print "===== Recovered Keyed Sequence Data ="

   source.list_keyed_sequence()

   source.flush_keyed_sequence(recover=True)

#---------------------------------------------------------------------

def recover_barcodes(source):
   print "Source - %s (%s)" % (source.Name, source.Type)

   source.init(rw=False)

   print "===== Barcode Serials ==============="

   source.list_barcodes()

   source.recover_barcodes()

   print "===== Recovered Barcode Serials ====="

   source.list_recovered_barcodes()

   source.flush_barcodes(recover=True)

#---------------------------------------------------------------------

#---------------------------------------------------------------------

def recover(source):
   if source.Type == 'CSV':
      recover_csv(source)
   elif source.Type == 'Keyed':
      recover_keyed(source)
   elif source.Type == 'KeyedSequence':
      recover_keyed_sequence(source)
   elif source.Type == 'Barcodes':
      recover_barcodes(source)

#---------------------------------------------------------------------

def usage():
   print __doc__

#---------------------------------------------------------------------

def main(argv):
   global debug_level
   global verbose_flg
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
      elif o == '-s':
         source_name      = a
      elif o == '-t':           # Deprecated term 'table'
         source_name      = a
      elif o == '-v':
         verbose_flg      = True
      elif o == '-V':
         print "Version: %s" % __version__
         return 0
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

   print
   print "Recovery of data in %s environment for data-server at %s:%s" % (environment, HOST, PORT)
   print

   if source_name:
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

         return 1
      else:
         source = sources[source_name]

      recover(source)

   else:
      print "Specify a data source table name!"
      return 2

   return 0

#---------------------------------------------------------------------

if __name__ == '__main__' or __name__ == sys.argv[0]:
   sys.exit(main(sys.argv[1:]))

#---------------------------------------------------------------------

"""
Revision History:

     Date     Who   Description
   --------   ---   --------------------------------------------------
   20110720   plh   Initial implementation

Problems to fix:

To Do:

Issues:

"""
