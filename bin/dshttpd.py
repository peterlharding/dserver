#!/usr/bin/env python
#
#       Author:  Peter Harding  <plh@performiq.com.au>
#                PerformIQ Pty. Ltd.
#
#                Mobile:  0418 375 085
#
#          Copyright (C) 1994-2011, Peter Harding
#                        All rights reserved
#
#--------------------------------------------------------------------------
"""
  Purpose:  HTTP Data Server Implementation

  Usage:

    To start normally:

      $ dshttpd.py -w /path/to/data/

    To start in debug mode (more detailed logging):

      $ dshttpd.py -d -w /path/to/data/

    To terminate:

      $ dshttpd.py -T -w /path/to/data/

      or

      $ dshttpd.py -T -p <pid>


    To check whether dserver is running:

      $ dshttpd.py -c -w /path/to/data/

  Notes:

    * Set the DSERVER_DIR environment variable to
      define dserver working (DATA) directory if you
      do not want to explicity specify the path to
      the data.

  Overview:

    Server side: Fire up an HTTPD to listen for requests

    This version has been extended to use the standard Python
    logging module.

    Add the delimiter to the INI file to allow use of alternate
    delimiters in transmitted data - so data with embedded commas
    can be used.
"""
#--------------------------------------------------------------------------

import os
import re
import csv
import sys
import time
import urllib
import urlparse
import cgi
import shutil
import mimetypes

import random
import getopt
import signal
import thread
import marshal
import logging
import socket
import threading
import SocketServer

#--------------------------------------------------------------------------

from datetime import datetime
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

#--------------------------------------------------------------------------

__id__            = "@(#)  dshttpd.py  [2.3.1]  2011-07-25"
__version__       = re.search(r'.*\[([^\]]*)\].*', __id__).group(1)
__all__           = ["RequestHandler"]

check_flg         = False
daemon_flg        = False
silent_flg        = False
terminate_flg     = False
verbose_flg       = False
wait_flg          = False

debug_level       = 0

HOST              = ''             #  Host server - '' means localhost
PORT              = 8000           #  Listen on a non-reserved port number
ENVIRONMENT       = 'SVT'

data_dir          = None
client_language   = None
log               = None
sources           = []
attributes        = {}

CONFIGFILE        = "dserver.ini"
LOGFILE           = "dserver.log"
PIDFILE           = "dserver.pid"

INVALID           = 'INVALID'

p_comment         = re.compile('^#')
p_args            = re.compile(r'([^\?]*)\?(.*)')

barcode_factors   = (8, 6, 4, 2, 3, 5, 9, 7)

#==========================================================================

class MultiThreadedHTTPServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass

#==========================================================================

class RequestHandler(BaseHTTPRequestHandler):

    """Simple HTTP request handler with GET and HEAD commands.

    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method.

    The GET and HEAD requests are identical except that the HEAD
    request omits the actual contents of the file.

    """

    server_version = "SimpleHTTP/" + __version__

    #-----------------------------------------------------------------------

    def do_GET(self):
        INFO('Host (%s) - Connected at %s' % (self.client_address[0], datetime.now()))

        """Serve a GET request."""

        if self.path == '/':  self.path = 'index.html'

        # print "[do_GET]  self.path [%s]" % self.path

        if self.client_address[0] == '10.3.7.214':
            print ">>>> %s <<<<" % self.path
            return

        m = p_args.search(self.path)

        if m:
            self.path = m.group(1)
            args =  {}
            for grp in m.group(2).split(r'&'):
                (k, v)   = grp.split('=')
                args[k]  = v
        
            # print "[do_GET]  args [%s]" % args
        else:
            args = None

        f = self.setup_headers(args)

        if f:
            self.wfile.write(f)

    #-----------------------------------------------------------------------

    def do_HEAD(self):
        """Serve a HEAD request."""
        print __doc__
        f = self.setup_headers()
        if f:
            f.close()

    #-----------------------------------------------------------------------

    def setup_headers(self, args):
        if args:
            if debug_level > 2:
                msg = args['msg']
                query = urllib.unquote(msg)
                reply = process(query)
            else:
                try:
                    msg = args['msg']
                    query = urllib.unquote(msg)
                    reply = process(query)
                except:
                    ERROR("[dserver::setup_headers]  Exception processing query '%s' args [%s]" % (query, args))
                    print "Exception processing message from args: [%s]" % args
                    reply = "*ERROR*"

            # print "[setup_headers]  ==> Reply [%s]" % reply

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            s = reply
            l = len(s)
            self.send_header("Content-Length", str(l))
            self.end_headers()
        else:
            s  = "<html><head><title>Served Tables</title></head><body>"
            s += "<hr>\n<table>\n"
            s += '<tr><td width="100">Name</th><th width="100">Type</th><th width="200">Notes</th></tr>\n'

            idx = 0

            for source in sources:
                if source.Type == 'Sequence':
                    s += '<tr><td><a href="?table=%s&action=GetNext&msg=GETN|%d">%s</a></td><td>%s</td><td>Starting value: %d</td></tr>\n' % (
                           source.Name, idx, source.Name, source.Type, source.Data)
                elif source.Type == 'Hashed':
                    keys = source.Data.keys()
                    s += '<tr><td><a href="?table=%s&action=GetNext&msg=GETH|%d|%s">%s</a></td><td>%s</td><td>Length: %d</td></tr>' % (
                           source.Name, idx, keys[random.randint(0, len(source.Data)-1)], source.Name, source.Type, len(source.Data))
                elif source.Type == 'Indexed':
                    s += '<tr><td><a href="?table=%s&action=GetNext&msg=GETI|%d|%d">%s</a></td><td>%s</td><td>Length: %d</td></tr>' % (
                           source.Name, idx, random.randint(0, len(source.Data)-1), source.Name, source.Type, len(source.Data))
                elif source.Type == 'Keyed':
                    keys = source.Data.keys()
                    grp  = keys[random.randint(0, len(source.Data)-1)]
                    l    = len(source.Data[grp].Data)
                    s += '<tr><td><a href="?table=%s&action=GetNext&msg=GETK|%d|%s">%s</a></td><td>%s</td><td>No groups: %d   Length \'%s\': %d</td></tr>' % (
                           source.Name, idx, grp, source.Name, source.Type, len(source.Data), grp, l)
                elif source.Type == 'Indexer':
                    s += '<tr><td><a href="?table=%s&action=GetNext&msg=GETN|%d">%s</a></td><td>%s</td><td>Data: %d</td></tr>' % (
                           source.Name, idx, source.Name, source.Type, source.Data)
                elif source.Type == 'Counter':
                    s += '<tr><td><a href="?table=%s&action=GetNext&msg=GETN|%d">%s</a></td><td>%s</td><td>Data: %d</td></tr>' % (
                           source.Name, idx, source.Name, source.Type, source.Data)
                else:  # CSV
                    s += '<tr><td><a href="?table=%s&action=GetNext&msg=GETN|%d">%s</a></td><td>%s</td><td>Length: %d</td></tr>' % (
                           source.Name, idx, source.Name, source.Type, len(source.Data) - source.Idx)
                idx += 1
            s += "</table><hr></body></html>\n"

            length = len(s)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(length))
            self.end_headers()
        return s

#==========================================================================

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

#--------------------------------------------------------------------------

class BarcodeGroup(Group):
    Prefix     = 'AA'
    Range      = 99
    Country    = 'AU'

    #-----------------------------------------------------------------------

    def __init__(self, name):
        (prefix, range, country) = name.split('-')

        self.Name       = name
        self.Prefix     = prefix
        self.Range      = int(range)
        self.Country    = country
        self.Serial     = None

    #-----------------------------------------------------------------------

    def __str__(self):
        s = "Grp %s  Serial %d" % (self.Name, self.Serial)
        return s

    #-----------------------------------------------------------------------

#--------------------------------------------------------------------------

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
        elif attributes.has_key('Delimiter'):
            self.Delimiter  = attributes['Delimiter']
        else:
            self.Delimiter  = ','

        rc = None

        if self.Type == "CSV":
            rc = self.init_csv()

        elif self.Type == "Sequence":
            rc = self.init_sequence()

        elif self.Type == "KeyedSequence":
            if attributes.has_key('TagDelimiter'):
                self.TagDelimiter  = attributes['TagDelimiter']
            else:
                self.TagDelimiter  = ':'
            rc = self.init_keyed_sequence()

        elif self.Type == "Hashed":
            if attributes.has_key('TagDelimiter'):
                self.TagDelimiter  = attributes['TagDelimiter']
            else:
                self.TagDelimiter  = ':'
            rc = self.init_hashed()

        elif self.Type == "Indexed":
            rc = self.init_indexed()

        elif self.Type == "Keyed":
            rc = self.init_keyed()

        elif self.Type == "Indexer":
            if attributes.has_key('start'):
                self.Data = attributes['start']
            else:
                self.Data = 1
            rc = True

        elif self.Type == "Counter":
            rc = self.init_counter()

        elif self.Type == "Barcodes":
            if attributes.has_key('TagDelimiter'):
                self.TagDelimiter  = attributes['TagDelimiter']
            else:
                self.TagDelimiter  = ':'
            rc = self.init_barcodes()

        if rc:
            self.Valid = True
        else:
            print "[dserver]  Bad source type [%s]" % source_type
            sys.exit(1)

        self.Size        = rc
        self.Attributes  = {
                               'Type'       : self.Type,
                               'Delimiter'  : self.Delimiter,
                               'Size'       : rc
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

    #-----------------------------------------------------------------------

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

    #-----------------------------------------------------------------------

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

    #-----------------------------------------------------------------------

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

            self.Data = no

        f.close()

        return True

    #-----------------------------------------------------------------------

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

    #-----------------------------------------------------------------------

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

     #-----------------------------------------------------------------------

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
                (tag, data) = line.split(self.TagDelimiter)

                tag = tag.strip()

                self.Data[tag] = data

        f.close()

        if debug_level > 2:
        	  INFO("Read in %d hashed rows - %s" % (len(self.Data), self.Name))
             if verbose_flg:  print "Read in %d hashed rows - %s" % (len(self.Data), self.Name)

        return True

    #-----------------------------------------------------------------------

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

        return True

    #-----------------------------------------------------------------------

    def init_indexer(self):
        self.Data = 0

        return True

    #-----------------------------------------------------------------------

    def init_counter(self):
        try:
            f = open(self.File, 'r')
        except IOError, e:
            sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
            sys.exit(1)

        self.Data = 1

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

            self.Data = int(no)

        f.close()

        return True

    #-----------------------------------------------------------------------

    def init_barcodes(self):
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
                (barcode_type, serial_no)    = line.split(self.TagDelimiter)

                barcode_type                 = barcode_type.strip()

                barcode_specification        = BarcodeGroup(barcode_type)
                barcode_specification.Serial = int(serial_no)
                self.Data[barcode_type]      = barcode_specification

        f.close()

        if debug_level > 2:
            INFO("Read in %d barcode groups - %s" % (len(self.Data), self.Name))
            if verbose_flg:  print "Read in %d barcode groups - %s" % (len(self.Data), self.Name)

        return True

    #-----------------------------------------------------------------------

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
            pass  # Do nothing
        elif self.Type == "Counter":
            self.flush_counter()
        elif self.Type == "Barcodes":
            self.flush_barcodes()

    #-----------------------------------------------------------------------

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

    #-----------------------------------------------------------------------

    def flush_sequence(self):
        os.system(self.BackupCmd)

        try:
            f = open(self.File, 'wb')
        except IOError, e:
            sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
            return 0

        for line in  self.Comments:
            f.write("%s\n" % line)

        f.write("%d\n" % self.Data)

        f.close()

    #-----------------------------------------------------------------------

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
            f.write("%s%s%s\n" % (key, self.TagDelimiter, self.Data[key]))

        f.close()

    #-----------------------------------------------------------------------

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

    #-----------------------------------------------------------------------

    def flush_hashed(self):
        pass

    #-----------------------------------------------------------------------

    def flush_indexed(self):
        pass

    #-----------------------------------------------------------------------

    def flush_counter(self):
        os.system(self.BackupCmd)

        try:
            f = open(self.File, 'wb')
        except IOError, e:
            sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
            return 0

        for line in  self.Comments:
            f.write("%s\n" % line)

        counter = self.Data + 1

        f.write("%d\n" % counter)

        f.close()

    #-----------------------------------------------------------------------

    def flush_barcodes(self):
        os.system(self.BackupCmd)

        try:
            f = open(self.File, 'wb')
        except IOError, e:
            sys.stderr.write('[dserver]  Open failed: %s\n' % str(e))
            return 0

        keys = self.Data.keys()

        keys.sort()

        for line in  self.Comments:
            f.write("%s\n" % line)

        for key in keys:
            f.write("%s%s%d\n" % (key, self.TagDelimiter, self.Data[key].Serial))

        f.close()

#==========================================================================

def INFO(msg):
    if log: log.info(' ' + msg)
    if verbose_flg: print "[dserver]  %s" % msg

#--------------------------------------------------------------------------

def ERROR(msg):
    if log: log.error(msg)
    if verbose_flg: print "[dserver]  %s" % msg

#--------------------------------------------------------------------------

def WARNING(msg):
    if log: log.warning('*****' + msg + '*****')
    if verbose_flg: print "[dserver]  %s" % msg

#==========================================================================

def read_config():
    global PORT, ENVIRONMENT

    config_file = CONFIGFILE

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

        elif (line.find("[Data]") != -1):
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

#--------------------------------------------------------------------------

def get_source_index(name):
    for i in range(len(sources)):
        if (sources[i].Name == name):
            return i

    return -1

#--------------------------------------------------------------------------

def process(s):
    global client_language

    msg = s.split("|")
    l   = len(msg)

    if debug_level > 1:  INFO("[dserver::process]  len %d  msg %s" % (l, msg))

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
            reply = "*OK*"

    elif (msg[0] == "REGI"):
        if (len(msg) != 2):
            ERROR("[dserver::process]  REGI -> Bad Message '%s'" % str(msg))
            reply = "*BAD*MESSAGE*"
        else:
            reply = "*OK*"

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
                elif source.Type in ["Sequence", "Indexer"]:
                    reply = "%d" % source.Data
                    source.Data += 1
                elif source.Type == "Counter":
                    reply = "%d" % source.Data
                else:
                    reply = "UNKNOWN"
            else:
                reply = "*BAD*HANDLE*"

            source.ufh.write("%s - %s\n" % (ts, reply))
            source.ufh.flush()
        else:
            ERROR("[dserver::process]  GETN -> Bad Message '%s'" % str(msg))
            reply = "*BAD*MESSAGE*"

        if debug_level > 2:  INFO("[dserver::process]  GETN -> %s" % reply)

    elif (msg[0] == "GETKS"):
        if (len(msg) == 3):
            hdl  = int(msg[1])
            key  = msg[2]

            try:
                source = sources[hdl]
            except:
                source = None

            if source != None:
                if source.Data.has_key(key):
                    reply             = "%d" % source.Data[key]
                    source.Data[key] += 1
                else:
                    reply = "*NO*VALID*KEY*"
            else:
                reply = "*BAD*SOURCE*INDEX*"

            source.ufh.write("%s - %s::%s\n" % (ts, key, reply))
            source.ufh.flush()
        else:
            ERROR("[dserver::process]  GETKS -> Bad Message '%s'" % str(msg))
            reply = "*BAD*MESSAGE*"

        if debug_level > 2:  INFO("[dserver::process]  GETKS %s -> %s" % (key, reply))

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
                        reply = "*Exhausted*"
                else:
                    reply = "*BAD*GROUP*"
            else:
                reply = "*BAD*HANDLE*"

            source.ufh.write("%s - %s::%s\n" % (ts, grp, reply))
            source.ufh.flush()
        else:
            ERROR("[dserver::process]  GETK -> Bad Message '%s'" % str(msg))
            reply = "*BAD*MESSAGE*"

        if debug_level > 2:  INFO("[dserver::process]  GETK %s -> %s" % (grp, reply))

    elif (msg[0] == "GETKR"):  # Pick random element from keyed group
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
                    len_data = len(g.Data)
                    if len_data > 0:
                        idx = random.randint(0, len_data - 1)
                        reply  = g.Data[idx]
                    else:
                        reply = "*Exhausted*"
                else:
                    reply = "*BAD*GROUP*"
  
            else:
                reply = "*BAD*HANDLE*"

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
                reply = "*BAD*HANDLE*"

            source.ufh.write("%s - %s::%s\n" % (ts, key, reply))
            source.ufh.flush()
        else:
            ERROR("[dserver::process]  GETH -> Bad Message", msg)
            return "*BAD*MESSAGE*"

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
                if idx >= 0:
                    try:
                        reply = source.Data[idx]
                    except:
                        reply = "*OUT*OF*RANGE*"
                else:
                    reply = "*INVALID*INDEX*"
            else:
                reply = "*BAD*HANDLE*"

            source.ufh.write("%s - %s::%s\n" % (ts, idx, reply))
            source.ufh.flush()
        else:
            ERROR("[dserver::process]  GETI -> Bad Message '%s'" % str(msg))
            reply = "*BAD*MESSAGE*"

        if debug_level > 2:  INFO("[dserver::process]  GETI %s -> %s" % (idx, reply))

    elif (msg[0] == "GETB"):
        if (len(msg) == 3):
            hdl         = int(msg[1])
            barcode_key = msg[2]

            try:
                source = sources[hdl]
            except:
                source = None

            if source != None:
                if source.Data.has_key(barcode_key):
                    barcode = source.Data[barcode_key]

                    no    = (int(barcode.Range) * 1000000) + barcode.Serial

                    bytes = list("%08d" % no)

                    sum   = 0

                    for idx in range(len(barcode_factors)):
                        sum += barcode_factors[idx] * int(bytes[idx])

                    chksum = sum % 11

                    print no, chksum

                    if chksum == 0:
                        chksum = 5
                    elif chksum == 1:
                        chksum = 0
                    else:
                        chksum = 11 - chksum

                    reply = '%s%08d%d%s' % (barcode.Prefix, no, chksum, barcode.Country)

                    barcode.Serial += 1
                else:
                    reply = "*NO*VALID*KEY*"
            else:
                reply = "*BAD*SOURCE*INDEX*"

            source.ufh.write("%s - %s::%s\n" % (ts, barcode_key, reply))
            source.ufh.flush()
        else:
            ERROR("[dserver::process]  GETB -> Bad Message '%s'" % str(msg))
            reply = "*BAD*MESSAGE*"

        if debug_level > 2:  INFO("[dserver::process]  GETB %s -> %s" % (barcode_key, reply))

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

                if debug_level > 1:  INFO("STOC %s" % data)

                reply = "1"
            else:
                reply = "*BAD*HANDLE*"
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
                else:  # Add a new group!
                    g                = Group(grp)
                    source.Data[grp] = g
                if g != None:
                    g.Data.append(data)
                    if debug_level > 1:  INFO("STOK %s %s" % (grp, data))
                    source.sfh.write("%s - %s::%s\n" % (ts, grp, data))
                    source.sfh.flush()
                reply = "1"
            else:
                reply = "*BAD*HANDLE*"
        else:
            ERROR("[dserver::process]  STOK -> Bad Message '%s'" % str(msg))
            reply = "*BAD*MESSAGE*"

        if debug_level > 2:  INFO("[dserver::process]  STOK %s %s -> %s" % (grp, data, reply))

    return reply

#--------------------------------------------------------------------------

def sig_term(signum, frame):
    "SIGTERM handler"

    shutdown()

#--------------------------------------------------------------------------

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
    except OSError, e:
        ERROR('Unlink failed: %s' % str(e))
        sys.exit(1)

    sys.exit(0)

#--------------------------------------------------------------------------

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

#--------------------------------------------------------------------------

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

#--------------------------------------------------------------------------

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

#--------------------------------------------------------------------------

def init_logging():
    global log

    log  = logging.getLogger('dserver')
    hdlr = logging.FileHandler(LOGFILE)
    fmtr = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    hdlr.setFormatter(fmtr)
    log.addHandler(hdlr)
    log.setLevel(logging.INFO)

    INFO("Server startup at %s" % datetime.now())

#--------------------------------------------------------------------------

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

    print "[dshttpd]  Listening on port %s - Data from %s/%s" % (PORT, os.getcwd(), ENVIRONMENT)

    try:
        httpd = MultiThreadedHTTPServer((HOST, PORT), RequestHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        httpd.socket.close()
        shutdown()
        print time.asctime(), "Server Stops - %s:%s" % (HOST, PORT)

#--------------------------------------------------------------------------

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

#--------------------------------------------------------------------------

def check():
    pid = check_running()

    if pid:
        print "[dserver]  Server already running! (pid = %d)" % pid
        sys.exit(0)
    else:
        print "[dserver]  Server not running"

#==========================================================================

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

    print wrk_path

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

#--------------------------------------------------------------------------

if __name__ == '__main__' or __name__ == sys.argv[0]:
    try:
        sys.exit(main())
    except KeyboardInterrupt, e:
        print "[dserver]  Interrupted!"
        shutdown()

#--------------------------------------------------------------------------

"""
Revision History:

      Date     Who   Description
    --------   ---   -----------------------------------------------------
    20070419   plh   Initial implementation
    20100714   plh   Added Counter type
    20110630   plh   Added KeyedSequence type
    20110630   plh   Added Barcode type
    20110801   plh   Updated to use Threaded HTTPD class

Problems to fix:

To Do:

Issues:

"""

