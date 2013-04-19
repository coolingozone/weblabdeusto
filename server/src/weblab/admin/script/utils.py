#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 onwards University of Deusto
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of contributions made by many individuals,
# listed below:
#
# Author: Pablo Orduña <pablo@ordunya.com>
#         Luis Rodriguez <luis.rodriguez@opendeusto.es>
#

import os
import sys

def check_dir_exists(directory, parser = None):
    if not os.path.exists(directory):
        if parser is not None:
            parser.error("ERROR: Directory %s does not exist" % directory)
        else:
            print >> sys.stderr, "ERROR: Directory %s does not exist" % directory
        sys.exit(-1)
    if not os.path.isdir(directory):
        if parser is not None:
            parser.error("ERROR: File %s exists, but it is not a directory" % directory)
        else:
            print >> sys.stderr, "ERROR: Directory %s does not exist" % directory
        sys.exit(-1)


