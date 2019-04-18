#!/usr/bin/python2.7
'''cPanels EasyApache 4 MultiPHP tools, terminal edition.'''
import sys
import os
import warnings
from getpass import getuser
from subprocess import Popen, PIPE, call
from inputargs import Parser
from api import API
import tempfile
import urllib
import json

try:
    from html import unescape  # python 3.4+
except ImportError:
    try:
        from html.parser import HTMLParser  # python 3.x (<3.4)
    except ImportError:
        from HTMLParser import HTMLParser  # python 2.x
    unescape = HTMLParser().unescape

parser = Parser()
args = parser.argparser.parse_args()
current_user = getuser()
api = API(args)


def main():

    if hasattr(args, 'mngr_subparser'):
        if args.mngr_subparser == 'get':
            api.manager_get()
    if hasattr(args, 'mngr_subparser'):
        if args.mngr_subparser == 'set':
            api.manager_set()
    
    if hasattr(args, 'ini_subparser'):
        if args.ini_subparser == 'get':
            api.ini_get()
        if args.ini_subparser == 'set':
            api.ini_set()
        if args.ini_subparser == 'edit':
            api.ini_edit()
     
    #determine_uapi_access()
    #print(run_cmd('whmapi1','listaccts', []))
    #print(api.call('uapi','domains_data',[],module='DomainInfo'))
    # start the selected module code
    # args.func()

def determine_uapi_access():
    '''this program needs to run uapi commands differently if ran as user, or as root, and needs to exit if ran as anything else (like a non-cPanel linux user)'''
    global CURRENT_USER
    CURRENT_USER = getuser()
    print(CURRENT_USER)
    if CURRENT_USER != "root":
        # this testing command is kinda arbitrary, but list_features is a decent one to use since it should work on any real cPanel user
        testing_cmd = ['uapi', 'Features', 'list_features', '--output=json']
        data, error = Popen(
            testing_cmd, 
            stdout=PIPE, 
            stderr=PIPE
            ).communicate()
        if error == '':
            data = json.loads(data)
            if args.verbose:
                print('UAPI Access Test STDOUT:\n')
                print(data)
                
        if error != '':
            if "Failed to load cPanel user file for" in error:
                sys.exit("This needs to be ran as either root, or as the cPanel user you wish to modify.")
    else:
        testing_cmd = ['uapi', 'Features', 'list_features', '--user=root', '--output=json']
        data, error = Popen(
            testing_cmd, 
            stdout=PIPE, 
            stderr=PIPE,
            ).communicate()
        if error == '':
            data = json.loads(data)
            if args.verbose:
                print('UAPI Access Test STDOUT:\n')
                print(data)
        if error != '':
            print(error)
            sys.exit(error)

if __name__ == '__main__':
    main()
