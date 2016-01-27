Overview
========

Python based Data Server to provide parameterized data to LoadRunner scripts.

Starting the Server
===================

Socket Server Version
---------------------

Ensure the python script - dserver.py  is in your path and then run it
with the -D option (run as a daemon):

 $ dserver.py -D

HTTPD Server Version
--------------------

Ensure the python script - dhttpd.py  is in your path and then run it
with the -D option (run as a daemon):

 $ dshttpd.py -D

A Makefile is provided atthe root of the project tree which provides

 $ make start


Stopping the Server
===================

Run the python script with the -T option (Terminate):

 $ dserver.py -D

or:

 $ dshttpd.py -D


Or using the Makefile:

 $ make stop

Other Components
================

The dcl directory contains the data server client components used with LoadRunner C scripts.

In particular, it contains the DLL - dcl.dll - which is linked into LoadRunner 
scripts.

The version in the dcl folder is a version built with VisualStudio 2005 and requires that the MS Redistributable package -  vcredist_v2005.exe - be applied.

Source code for this is contained in the src sub-folder of this repository.

A Windows executable - dcl_test.exe - is also provided to directly test the DLL with a running data server - dserver.py - instance.  By default this test program expects the data server to be listening on port 9578.

Source for this test executable is also provided in the src directory.

Testing the DataSever
=====================

Several options are available:

1)  Within cygwin use the python script - tst.py - or one of its varians
2)  from Windows use the exe - dcl.exe - bin/dcl.exe


Transcript of tst.py retrieving UserId and Password from Globals table:

  $ ./tst.py -s Globals -I UserId
  No DSERVER_DIR environment variable set!
  Attempting to use local DATA directory...

  Testing data-server at dserver:9578

  Connected to data-server on port 9578
  My PID is 4360
  Data type "Globals" registered (with index) 0 ...
     ... has attributes {'Delimiter': ',', 'Type': 'Hashed', 'Size': 3}

  Retrieving hash entry for value "UserId"
  Buffer is "['me']"
  Field  0: "me"


  $ ^Username^Password
  ./tst.py -s Globals -I Password
  No DSERVER_DIR environment variable set!
  Attempting to use local DATA directory...

  Testing data-server at dserver:9578

  Connected to data-server on port 9578
  My PID is 2384
  Data type "Globals" registered (with index) 0 ...
     ... has attributes {'Delimiter': ',', 'Type': 'Hashed', 'Size': 3}

  Retrieving hash entry for value "Password"
  Buffer is "['password']"
  Field  0: "password"


Enhancements
============

Some improvements I have thought of implementing and not got around to:

1) Add a timer to shut the dserver down after a period of extended inactivity...

   If you forget to shut it down and the system running the server daemon
   shuts down or the data server crashes you will not get the data
   flushed back to disk.  In this case you will need to reconstruct
   the consumed data tables from the .Used files (in DATA/tmp/)

2) Add a flush files call

   This would minimize the risk of having to reconstruct data when the
   dserver shuts down without successfully flushing the data back to
   disk.

3) Add a call to increment RunNo

   In some situations I tag each run with a monotonically increasing
   RunNo.  Currently I manually increment this between runs - which
   requires shutding down and restarting the data server (which also
   guarantees data is synced to disk between test runs).

4) Implement a Python module so that low level code for both server and client
   scripts is common.

   Haven't tough enough about this to come to any conclusions about what
   would make sense.

   


