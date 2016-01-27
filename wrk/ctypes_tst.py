#!/usr/bin/env python

#from ctypes import *

import sys
import ctypes
import pprint

# pprint.pprint(ctypes.__dict__)

# print ctypes.windll.kernel32 # doctest: +WINDOWS

libc = ctypes.cdll.msvcrt # doctest: +WINDOWS

print libc.time(None)


x = ctypes.c_int(255)

print x.value


p = ctypes.create_string_buffer(3)      # create a 3 byte buffer, initialized to NUL bytes

print ctypes.sizeof(p), repr(p.raw)

c = ctypes.c_char_p("Hello, World")

print ">> %s" % c.value

printf = libc.printf

printf("Hello, %s\n", "World!")

sys.stdout.write("XXXX\n")

printf("An int %d, a double %f\n", 1234, ctypes.c_double(3.14))


class Bottles(object):
   def __init__(self, number):
      self._as_parameter_ = number

   def __str__(self):
      return "%d" % self._as_parameter_

bottles = Bottles(42)

print "bottles -> ", bottles

printf("%d bottles of beer\n", bottles)




print '*END*'

"""
{'ARRAY': <function ARRAY at 0x7ff2c6bc>,
 'ArgumentError': <class 'ctypes.ArgumentError'>,
 'Array': <type '_ctypes.Array'>,
 'BigEndianStructure': <class 'ctypes._endian.BigEndianStructure'>,
 'CDLL': <class 'ctypes.CDLL'>,
 'CFUNCTYPE': <function CFUNCTYPE at 0x7ff2c534>,
 'DEFAULT_MODE': 0,
 'LibraryLoader': <class 'ctypes.LibraryLoader'>,
 'LittleEndianStructure': <type '_ctypes.Structure'>,
 'POINTER': <function POINTER at 0x7ff2c5a4>,
 'PYFUNCTYPE': <function PYFUNCTYPE at 0x7ff2c6f4>,
 'PyDLL': <class 'ctypes.PyDLL'>,
 'RTLD_GLOBAL': 4,
 'RTLD_LOCAL': 0,
 'SetPointerType': <function SetPointerType at 0x7ff2c64c>,
 'Structure': <type '_ctypes.Structure'>,
 'Union': <type '_ctypes.Union'>,
 '_CFuncPtr': <type '_ctypes.CFuncPtr'>,
 '_FUNCFLAG_CDECL': 1,
 '_FUNCFLAG_PYTHONAPI': 4,
 '_Pointer': <type '_ctypes._Pointer'>,
 '_SimpleCData': <type '_ctypes._SimpleCData'>,
 '__builtins__': {'ArithmeticError': <type 'exceptions.ArithmeticError'>,
                  'AssertionError': <type 'exceptions.AssertionError'>,
                  'AttributeError': <type 'exceptions.AttributeError'>,
                  'BaseException': <type 'exceptions.BaseException'>,
                  'DeprecationWarning': <type 'exceptions.DeprecationWarning'>,
                  'EOFError': <type 'exceptions.EOFError'>,
                  'Ellipsis': Ellipsis,
                  'EnvironmentError': <type 'exceptions.EnvironmentError'>,
                  'Exception': <type 'exceptions.Exception'>,
                  'False': False,
                  'FloatingPointError': <type 'exceptions.FloatingPointError'>,
                  'FutureWarning': <type 'exceptions.FutureWarning'>,
                  'GeneratorExit': <type 'exceptions.GeneratorExit'>,
                  'IOError': <type 'exceptions.IOError'>,
                  'ImportError': <type 'exceptions.ImportError'>,
                  'ImportWarning': <type 'exceptions.ImportWarning'>,
                  'IndentationError': <type 'exceptions.IndentationError'>,
                  'IndexError': <type 'exceptions.IndexError'>,
                  'KeyError': <type 'exceptions.KeyError'>,
                  'KeyboardInterrupt': <type 'exceptions.KeyboardInterrupt'>,
                  'LookupError': <type 'exceptions.LookupError'>,
                  'MemoryError': <type 'exceptions.MemoryError'>,
                  'NameError': <type 'exceptions.NameError'>,
                  'None': None,
                  'NotImplemented': NotImplemented,
                  'NotImplementedError': <type 'exceptions.NotImplementedError'>,
                  'OSError': <type 'exceptions.OSError'>,
                  'OverflowError': <type 'exceptions.OverflowError'>,
                  'PendingDeprecationWarning': <type 'exceptions.PendingDeprecationWarning'>,
                  'ReferenceError': <type 'exceptions.ReferenceError'>,
                  'RuntimeError': <type 'exceptions.RuntimeError'>,
                  'RuntimeWarning': <type 'exceptions.RuntimeWarning'>,
                  'StandardError': <type 'exceptions.StandardError'>,
                  'StopIteration': <type 'exceptions.StopIteration'>,
                  'SyntaxError': <type 'exceptions.SyntaxError'>,
                  'SyntaxWarning': <type 'exceptions.SyntaxWarning'>,
                  'SystemError': <type 'exceptions.SystemError'>,
                  'SystemExit': <type 'exceptions.SystemExit'>,
                  'TabError': <type 'exceptions.TabError'>,
                  'True': True,
                  'TypeError': <type 'exceptions.TypeError'>,
                  'UnboundLocalError': <type 'exceptions.UnboundLocalError'>,
                  'UnicodeDecodeError': <type 'exceptions.UnicodeDecodeError'>,
                  'UnicodeEncodeError': <type 'exceptions.UnicodeEncodeError'>,
                  'UnicodeError': <type 'exceptions.UnicodeError'>,
                  'UnicodeTranslateError': <type 'exceptions.UnicodeTranslateError'>,
                  'UnicodeWarning': <type 'exceptions.UnicodeWarning'>,
                  'UserWarning': <type 'exceptions.UserWarning'>,
                  'ValueError': <type 'exceptions.ValueError'>,
                  'Warning': <type 'exceptions.Warning'>,
                  'ZeroDivisionError': <type 'exceptions.ZeroDivisionError'>,
                  '__debug__': True,
                  '__doc__': "Built-in functions, exceptions, and ...",
                  '__import__': <built-in function __import__>,
                  '__name__': '__builtin__',
                  'abs': <built-in function abs>,
                  'all': <built-in function all>,
                  'any': <built-in function any>,
                  'apply': <built-in function apply>,
                  'basestring': <type 'basestring'>,
                  'bool': <type 'bool'>,
                  'buffer': <type 'buffer'>,
                  'callable': <built-in function callable>,
                  'chr': <built-in function chr>,
                  'classmethod': <type 'classmethod'>,
                  'cmp': <built-in function cmp>,
                  'coerce': <built-in function coerce>,
                  'compile': <built-in function compile>,
                  'complex': <type 'complex'>,
                  'copyright': 'Copyright (c) 2001-2007 ...',
                  'delattr': <built-in function delattr>,
                  'dict': <type 'dict'>,
                  'dir': <built-in function dir>,
                  'divmod': <built-in function divmod>,
                  'enumerate': <type 'enumerate'>,
                  'eval': <built-in function eval>,
                  'execfile': <built-in function execfile>,
                  'exit': Use exit() or Ctrl-D (i.e. EOF) to exit,
                  'file': <type 'file'>,
                  'filter': <built-in function filter>,
                  'float': <type 'float'>,
                  'frozenset': <type 'frozenset'>,
                  'getattr': <built-in function getattr>,
                  'globals': <built-in function globals>,
                  'hasattr': <built-in function hasattr>,
                  'hash': <built-in function hash>,
                  'help': "Type help() ...",
                  'hex': <built-in function hex>,
                  'id': <built-in function id>,
                  'input': <built-in function input>,
                  'int': <type 'int'>,
                  'intern': <built-in function intern>,
                  'isinstance': <built-in function isinstance>,
                  'issubclass': <built-in function issubclass>,
                  'iter': <built-in function iter>,
                  'len': <built-in function len>,
                  'license': Type license() to see the full license text,
                  'list': <type 'list'>,
                  'locals': <built-in function locals>,
                  'long': <type 'long'>,
                  'map': <built-in function map>,
                  'max': <built-in function max>,
                  'min': <built-in function min>,
                  'object': <type 'object'>,
                  'oct': <built-in function oct>,
                  'open': <built-in function open>,
                  'ord': <built-in function ord>,
                  'pow': <built-in function pow>,
                  'property': <type 'property'>,
                  'quit': Use quit() or Ctrl-D (i.e. EOF) to exit,
                  'range': <built-in function range>,
                  'raw_input': <built-in function raw_input>,
                  'reduce': <built-in function reduce>,
                  'reload': <built-in function reload>,
                  'repr': <built-in function repr>,
                  'reversed': <type 'reversed'>,
                  'round': <built-in function round>,
                  'set': <type 'set'>,
                  'setattr': <built-in function setattr>,
                  'slice': <type 'slice'>,
                  'sorted': <built-in function sorted>,
                  'staticmethod': <type 'staticmethod'>,
                  'str': <type 'str'>,
                  'sum': <built-in function sum>,
                  'super': <type 'super'>,
                  'tuple': <type 'tuple'>,
                  'type': <type 'type'>,
                  'unichr': <built-in function unichr>,
                  'unicode': <type 'unicode'>,
                  'vars': <built-in function vars>,
                  'xrange': <type 'xrange'>,
                  'zip': <built-in function zip>},
 '__doc__': 'create and manipulate C data types in Python',
 '__file__': '/usr/lib/python2.5/ctypes/__init__.pyc',
 '__name__': 'ctypes',
 '__path__': ['/usr/lib/python2.5/ctypes'],
 '__version__': '1.0.2',
 '_c_functype_cache': {(<class 'ctypes.py_object'>,
                         (<class 'ctypes.c_void_p'>,
                          <class 'ctypes.c_long'>)):
                            <class 'ctypes.CFunctionType'>,
                       (<class 'ctypes.c_void_p'>,
                         (<class 'ctypes.c_void_p'>,
                          <class 'ctypes.c_long'>,
                          <class 'ctypes.c_ulong'>)):
                            <class 'ctypes.CFunctionType'>,
                       (<class 'ctypes.c_void_p'>,
                          (<class 'ctypes.c_void_p'>,
                          <class 'ctypes.c_void_p'>,
                          <class 'ctypes.c_ulong'>)):
                          <class 'ctypes.CFunctionType'>},
 '_calcsize': <function calcsize at 0x7ff2c3ac>,
 '_cast': <CFunctionType object at 0x7ff735dc>,
 '_cast_addr': 1704224672,
 '_check_size': <function _check_size at 0x7ff2c56c>,
 '_ctypes_version': '1.0.2',
 '_dlopen': <built-in function dlopen>,
 '_endian': <module 'ctypes._endian' from '/usr/lib/python2.5/ctypes/_endian.pyc'>,
 '_memmove_addr': 1704257232,
 '_memset_addr': 1704257200,
 '_os': <module 'os' from '/usr/lib/python2.5/os.pyc'>,
 '_pointer_type_cache': {None: <class 'ctypes.c_void_p'>,
                         <class 'ctypes.c_char'>: <class 'ctypes.LP_c_char'>,
                         <class 'ctypes.c_wchar'>: <class 'ctypes.LP_c_wchar'>},
 '_string_at': <CFunctionType object at 0x7ff7364c>,
 '_string_at_addr': 1704224624,
 '_sys': <module 'sys' (built-in)>,
 '_wstring_at': <CFunctionType object at 0x7ff736bc>,
 '_wstring_at_addr': 1704228496,
 'addressof': <built-in function addressof>,
 'alignment': <built-in function alignment>,
 'byref': <built-in function byref>,
 'c_buffer': <function c_buffer at 0x7ff2c4fc>,
 'c_byte': <class 'ctypes.c_byte'>,
 'c_char': <class 'ctypes.c_char'>,
 'c_char_p': <class 'ctypes.c_char_p'>,
 'c_double': <class 'ctypes.c_double'>,
 'c_float': <class 'ctypes.c_float'>,
 'c_int': <class 'ctypes.c_long'>,
 'c_int16': <class 'ctypes.c_short'>,
 'c_int32': <class 'ctypes.c_long'>,
 'c_int64': <class 'ctypes.c_longlong'>,
 'c_int8': <class 'ctypes.c_byte'>,
 'c_long': <class 'ctypes.c_long'>,
 'c_longlong': <class 'ctypes.c_longlong'>,
 'c_short': <class 'ctypes.c_short'>,
 'c_size_t': <class 'ctypes.c_ulong'>,
 'c_ubyte': <class 'ctypes.c_ubyte'>,
 'c_uint': <class 'ctypes.c_ulong'>,
 'c_uint16': <class 'ctypes.c_ushort'>,
 'c_uint32': <class 'ctypes.c_ulong'>,
 'c_uint64': <class 'ctypes.c_ulonglong'>,
 'c_uint8': <class 'ctypes.c_ubyte'>,
 'c_ulong': <class 'ctypes.c_ulong'>,
 'c_ulonglong': <class 'ctypes.c_ulonglong'>,
 'c_ushort': <class 'ctypes.c_ushort'>,
 'c_void_p': <class 'ctypes.c_void_p'>,
 'c_voidp': <class 'ctypes.c_void_p'>,
 'c_wchar': <class 'ctypes.c_wchar'>,
 'c_wchar_p': <class 'ctypes.c_wchar_p'>,
 'cast': <function cast at 0x7ff2c8ec>,
 'cdll': <ctypes.LibraryLoader object at 0x7ff349ec>,
 'create_string_buffer': <function create_string_buffer at 0x7ff2c4c4>,
 'create_unicode_buffer': <function create_unicode_buffer at 0x7ff2c614>,
 'memmove': <CFunctionType object at 0x7ff734fc>,
 'memset': <CFunctionType object at 0x7ff7356c>,
 'pointer': <function pointer at 0x7ff2c684>,
 'py_object': <class 'ctypes.py_object'>,
 'pydll': <ctypes.LibraryLoader object at 0x7ff34a2c>,
 'pythonapi': <PyDLL 'libpython2.5.dll', handle 6cac0000 at 7ff34a4c>,
 'resize': <built-in function resize>,
 'set_conversion_mode': <built-in function set_conversion_mode>,
 'sizeof': <built-in function sizeof>,
 'string_at': <function string_at at 0x7ff2c924>,
 'wstring_at': <function wstring_at at 0x7ff2c95c>}
"""
