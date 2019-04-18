#!/usr/bin/python2.7

from inputargs import Parser
from api import API

parser = Parser()
args = parser.argparser.parse_args()
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
     
if __name__ == '__main__':
    main()
