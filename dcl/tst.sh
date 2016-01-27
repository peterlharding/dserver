#!/bin/sh
#
#-------------------------------------------------------------------------

set -x

PATH=.

HOST=dserver
PORT=9567

if [ $# -eq 1 ]; then
   HOST=$1
fi

if [ $# -eq 2 ]; then
   HOST=$1
   PORT=$2
fi


${PATH}/dcl_test.exe -h $HOST -p $PORT -s Test -i 12

${PATH}/dcl_test.exe -h $HOST -p $PORT -s Sequence -n 3

${PATH}/dcl_test.exe -h $HOST -p $PORT -s Globals -I Password
