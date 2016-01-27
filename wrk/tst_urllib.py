#!/usr/bin/env python

import urllib

s = 'GETN%7C4'

print urllib.unquote(s)

s = 'GETN|4'

print urllib.unquote(s)



