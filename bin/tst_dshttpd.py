#!/usr/bin/env python
#
#-------------------------------------------------------------------------------
"""

  Usage:

    $ tst_dshttpd.py -i 10
    $ tst_dshttpd.py -k key




"""
#-------------------------------------------------------------------------------


import httplib
import random
import urllib

#-------------------------------------------------------------------------------

HOST      = 'dserver'
PORT      = 9578

HOST_STR  = '%s:%d' %(HOST, PORT)

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

def tst_indexed(no):
    conn = httplib.HTTPConnection(HOST_STR)

    URL  = '/?msg=GETI|3|%d' % no

    conn.request("GET", URL, None, get_headers)

    rc   = conn.getresponse()

    # print rc.__dict__
    print rc.status, rc.reason
    # print rc.msg

    data = rc.read()

    print "Data: [%s]" % data

    conn.close()

#-------------------------------------------------------------------------------

def tst_indexer():
    conn = httplib.HTTPConnection(HOST_STR)

    URL  = '/?msg=GETN|0'

    conn.request("GET", URL, None, get_headers)

    rc   = conn.getresponse()

    # print rc.__dict__
    print rc.status, rc.reason
    # print rc.msg

    data = rc.read()

    print "Data: [%s]" % data

    conn.close()

#-------------------------------------------------------------------------------

def tst_keyed(key):
    conn = httplib.HTTPConnection(HOST_STR)

    URL  = '/?msg=GETK|6|%s' % key

    conn.request("GET", URL, None, get_headers)

    rc   = conn.getresponse()

    # print rc.__dict__
    print rc.status, rc.reason
    # print rc.msg

    data = rc.read()

    print "Data: [%s]" % data

    conn.close()

#-------------------------------------------------------------------------------

def tst_keyed_random(key):
    conn = httplib.HTTPConnection(HOST_STR)

    URL    = '/?msg=GETKR|5|%s' % key

    conn.request("GET", URL, None, get_headers)

    rc = conn.getresponse()

    # print rc.__dict__
    print rc.status, rc.reason
    # print rc.msg

    data = rc.read()

    print "Data: [%s]" % data

    conn.close()

#-------------------------------------------------------------------------------

def tst_barcodes(key):
    conn = httplib.HTTPConnection(HOST_STR)

    URL  = '/?msg=GETB|0|%s' % key

    conn.request("GET", URL, None, get_headers)

    rc   = conn.getresponse()

    # print rc.__dict__
    print rc.status, rc.reason
    # print rc.msg

    data = rc.read()

    print "Data: [%s]" % data

    conn.close()

#-------------------------------------------------------------------------------

def get_run_no():
    conn = httplib.HTTPConnection(HOST_STR)

    URL  = '/?msg=GETN|1'

    conn.request("GET", URL, None, get_headers)

    rc   = conn.getresponse()

    # print rc.__dict__
    print rc.status, rc.reason
    # print rc.msg

    data = rc.read()

    print "Data: [%s]" % data

    conn.close()

#-------------------------------------------------------------------------------



#------------------------------------------------------------------------------

def usage():
    print __doc__

#------------------------------------------------------------------------------

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
    global HOST_STR
    global ds_dir
    global data_dir

    no                = 1
    host              = None
    port              = None
    source_name       = None

    use_csv           = False
    use_sequence      = False
    use_indexed       = False
    use_indexer       = False
    use_keyed         = False

    store_flg         = False

    try:
        opts, args = getopt.getopt(argv, "dD:hH:i:I:k:n:P:rs:S:t:Tw:vV?")
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
	    use_indexed      = True
            index            = int(a)
        elif o == '-I':            # Assuming a string index! (i.e. a hash!)
            hashed           = True
            hash_key         = a
        elif o == '-k':
	    use_keyed        = True
            key              = a
        elif o == '-n':
            no               = int(a)
        elif o == '-r':
            get_run_no()
	    exit(0)
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

    # read_config()

    if host or port:
         if host:
              HOST = host

         if port:
              PORT = port

         HOST_STR  = '%s:%d' %(HOST, PORT)

    if use_indexed:

        tst_indexed(5)

    elif use_indexer:

        tst_indexer()

    elif use_keyed:

        tst_keyed()

    elif use_barcode:

        tst_barcodes('AB-89-CA')

    elif random_keyed:

        tst_keyed_random("AUPERB")

    else:

        tst_csv()

    print
    print "Testing dshttpd at %s:%s" % (HOST, PORT)
    print


#------------------------------------------------------------------------------

if __name__ == '__main__' or __name__ == sys.argv[0]:
    sys.exit(main(sys.argv[1:]))

#------------------------------------------------------------------------------

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



#-------------------------------------------------------------------------------

