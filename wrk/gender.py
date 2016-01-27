#!/usr/bin/env python
#
#  $Id:$
#
#-------------------------------------------------------------------------------

"""
Transform CSV data to generate LoadRunner parameter files
"""

import os
import csv
import sys
import getopt
import random
import datetime

#---------------------------------------------------------------------

max_flg       = False
random_flg    = False
verbose_flg   = False

debug_cnt     = 0

__version__   = '1.0.0'

first_names   = 'FirstNames.csv'
names_in      = 'Names_10K.dat'
names_out     = 'Names_10K.NEW'

#=====================================================================

class Name:
   pass

   #---------------------------------------------------------------

   def __init__(self, l):
      self.Honorific = l[0]
      self.FirstName = l[1]
      self.Surname   = l[2]
      self.Facility  = l[3]

   #---------------------------------------------------------------

   def __str__(self):
      return "%s,%s,%s,%s" % (self.Honorific,
               self.FirstName,
               self.Surname,
               self.Facility)

#=====================================================================
#----- Read in source data for transformation ------------------------

def set_gender():
   f_gender    = open(first_names, 'r')
   f_names_in  = open(names_in, 'r')
   f_names_out = open(names_out, 'w')

   reader = csv.reader(f_gender)

   cnt        = 0
   gender     = {}

   for row in reader:
      cnt += 1
      gender[row[1]] = row[0]

   f_gender.close()

   print "Read in %d first names..." % cnt

   reader = csv.reader(f_names_in)

   cnt        = 0

   names = []

   for row in reader:
      cnt += 1

      if cnt == 1:
         continue  # Skip heading!

      name = Name(row)

      name.Honorific = gender[name.FirstName]

      names.append(name)

   f_names_in.close()

   while True:
      l = len(names)

      print l

      if l == 0:
         break

      idx = random.randint(0, l - 1)

      name = names.pop(idx)

      f_names_out.write('%s\n' % name)

   f_names_out.close()

#-------------------------------------------------------------------------------

USAGE = """\

  Usage:

     $ ./gender.py [-d] [-v] [-f <filename>]

"""

def usage():
   sys.stderr.write(USAGE)

#-------------------------------------------------------------------------------

def main(argv):
   global debug_cnt
   global verbose_flg
   global file

   #----- Process command line arguments ----------------------------

   try:
      opts, args = getopt.getopt(argv, "df:hv",
                 ["debug", "file=", "help", "verbose"])
   except getopt.GetoptError:
      usage()
      sys.exit(2)
   else:
      for opt, arg in opts:
         if opt in ("-d", "--debug"):
            debug_cnt    += 1
         elif opt in ("-f", "--file"):
            logfile       = arg
         elif opt in ("-h", "--help"):
            usage()
            sys.exit(0)
         elif opt in ("-v", "--verbose"):
            verbose_flg   = True

   set_gender()

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main(sys.argv[1:])

#-------------------------------------------------------------------------------



