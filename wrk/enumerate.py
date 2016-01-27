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

source_data   = 'src.csv'
dest_data     = 'dest.dat'

#----- Read in source data for transformation ------------------------

def transform():

   data_in  = open(source_data, 'r')
   data_out   = open(dest_data, 'w')

   reader = csv.reader(data_in)

   cnt        = 0
   n          = 0
   current_dc = None
   rows       = []

   for row in reader:
      cnt += 1

      if (cnt == 1):
         n = int(row[3])
      else:
         n += 1

      data_out.write('%s,%s,%s,%d\n' % (row[0], row[1], row[2], n))

   data_in.close()
   data_out.close()

#-------------------------------------------------------------------------------

USAGE = """\

  Usage:

     $ ./tf.py [-d] [-v] [-f <filename>]

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

   transform()

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main(sys.argv[1:])

#-------------------------------------------------------------------------------



