#!/usr/bin/env python
#
#
#-------------------------------------------------------------------------------


import sys
import ctypes
import pprint

#-------------------------------------------------------------------------------

#from ctypes import *

#-------------------------------------------------------------------------------

# print ctypes.windll.kernel32 # doctest: +WINDOWS

#-------------------------------------------------------------------------------

#dserver = ctypes.cdll.LoadLibrary('dcl')
dserver = ctypes.CDLL('dcl')

pprint.pprint(dserver.__dict__)

print type(dserver)

#-------------------------------------------------------------------------------

dserver.dsInit.restype         = ctypes.c_char_p
dserver.dsInit.argtypes        = [ctypes.c_char_p, ctypes.c_int]

dserver.dsRegister.restype     = ctypes.c_int
dserver.dsRegister.argtypes    = [ctypes.c_char_p]

dserver.dsGetNext.restype      = ctypes.c_char_p
dserver.dsGetNext.argtypes     = [ctypes.c_int]

dserver.dsGetKeyed.restype     = ctypes.c_char_p
dserver.dsGetKeyed.argtypes    = [ctypes.c_int, ctypes.c_char_p]

dserver.dsGetIndexed.restype   = ctypes.c_char_p
dserver.dsGetIndexed.argtypes  = [ctypes.c_int, ctypes.c_int]

dserver.dsStore.restype        = ctypes.c_int
dserver.dsStore.argtypes       = [ctypes.c_int, ctypes.c_char_p]

#-------------------------------------------------------------------------------

s  = 100 * ' '

dserver.get_buffered(1, s, 100)

# print s

dserver.dsInit('localhost', 9578)

h_seq = dserver.dsRegister('Sequence')

seq = dserver.dsGetNext(h_seq)

print seq

h_address = dserver.dsRegister('Address')

address = dserver.dsGetNext(h_address)

print address

str = "150 Queen Street,Melbourne,Victoria,3000"

rc = dserver.dsStore(h_address, str)

print rc

#-------------------------------------------------------------------------------


