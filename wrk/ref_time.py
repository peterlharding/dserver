#!/usr/bin/env python
#
#  $Id:$
#
#---------------------------------------------------------------------

import sys

#=====================================================================

def the_time():
   t = float(ref_time(FALSE)) * 0.001

   return t

#---------------------------------------------------------------------

def ref_time(flg):
   global start

   curr = datetime.now()

   if (flg):
      start  = curr
      t      = 0
   else:
      microsecond = (curr.microsecond - start.microsecond)
      second      = ((curr.second     - start.second) * 1000000)
      t           = (second + microsecond)/1000

   return t

#=====================================================================

def main():
   return 0

#---------------------------------------------------------------------

if __name__ == '__main__' or __name__ == sys.argv[0]:
   sys.exit(main())

#---------------------------------------------------------------------

"""
Revision History:

     Date     Who   Description
   --------   ---   --------------------------------------------------
   20031014   plh   Initial implementation

Problems to fix:

To Do:

Issues:

"""

