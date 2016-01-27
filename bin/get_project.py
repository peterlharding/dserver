#!/usr/bin/env python
#
#  Purpose:  Return the name of the project this instance is used with.
#
#  Assumes:  Data Server directory is copied into the project folder
#            and is run from here - to provide Data separation between
#            projects.
#
#-------------------------------------------------------------------------

import os

path = os.getcwd()

print path.split('/')[-2]


