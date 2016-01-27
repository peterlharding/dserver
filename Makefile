#
#  Maefile for working with data server
#
#---------------------------------------------------------------------

PROJECT = $(shell bin/get_project.py)

#DSERVER_DIR  = $(LR)/$(PROJECT)/dserver/DATA
DSERVER_DIR  = `pwd`/DATA

#---------------------------------------------------------------------

all:	start

#---------------------------------------------------------------------

start:
	bin/dserver.py -w $(DSERVER_DIR) -D 

stop:
	bin/dserver.py -T -w $(DSERVER_DIR)

htstart:
	# bin/dshttpd.py -w $(DSERVER_DIR) -dddd > dserver.log 2>&1 &
	bin/dshttpd.py -w $(DSERVER_DIR) -D

htstop:
	bin/dshttpd.py -T

debug:
	bin/dserver.py -d -w $(DSERVER_DIR) &

check:
	bin/dserver.py -c -w $(DSERVER_DIR)

#---------------------------------------------------------------------

reset:
	bin/dserver.py -T -w $(DSERVER_DIR)
	sleep 30
	-(cd DATA; make reset)
	bin/dserver.py -w $(DSERVER_DIR) &

#---------------------------------------------------------------------

clean:
	-/bin/rm -f *.pyc
	-(cd DATA; make clean)

#---------------------------------------------------------------------

tst:
	echo $(PROJECT)
	echo $(DSERVER_DIR)

#---------------------------------------------------------------------


