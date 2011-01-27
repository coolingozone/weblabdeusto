#!/usr/bin/env python
#-*-*- encoding: utf-8 -*-*-
#
# Copyright (C) 2005-2009 University of Deusto
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# This software consists of contributions made by many individuals, 
# listed below:
#
# Author: Pablo Orduña <pablo@ordunya.com>
#		  Luis Rodríguez <luis.rodriguez@opendeusto.es>
# 

####################################################
#
# This script must be run on a system with the
# vncpasswd command available, and on a user with enough 
# privileges to change the VNC password through it.
# Any call to http://(this-host):PORT/?sessionid=foo
# will change the VNC password to "foo". Is is noteworthy,
# however, that the maximum number of characters of a VNC
# password is 8. Though longer strings might be specified,
# any character after the eighth will be ignored.
# 

PORT        = 18080
PASSWD_PATH = "/usr/bin/vncpasswd"

####################################################

import pexpect
import time
import urllib
import traceback
import BaseHTTPServer

def change_password(new_passwd):
    """
    Changes the VNC password to the specified one using the vncpasswd tool,
    which should be available.
    """
    passwd = pexpect.spawn("%s" % (PASSWD_PATH))
    
    # Note: The password has to be at least 6 characters long. If a shorter password is
    # received vncpasswd fails and a not-so-intuitive error message results.
	
    # wait for password: to come out of passwd's stdout
    passwd.expect("Password: ")
    # send pass to passwd's stdin
    passwd.sendline(new_passwd)
    
    time.sleep(0.1)
    
    passwd.expect("Verify: ")
    passwd.sendline(new_passwd)
	
    time.sleep(0.1)
	
    passwd.expect(" (y/n)?")
    passwd.sendline("n");
    
    time.sleep(0.1)

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        _, query_args = urllib.splitquery(self.path)
        arguments = dict([ urllib.splitvalue(query_arg) for query_arg in query_args.split('&') ])
        session_id = arguments.get('sessionid')

        if session_id is None:
            self.send_error(400)
            self.end_headers()
            self.wfile.write("fail: sessionid argument is required")
        else:
            try:
                change_password(session_id)
            except Exception, e:
                traceback.print_exc()
                self.send_error(500)
                self.end_headers()
                self.wfile.write("Internal error: %s" % str(e))
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write("ok")
        self.wfile.close()

server = BaseHTTPServer.HTTPServer(('',PORT), RequestHandlerClass = Handler)
server.serve_forever()

