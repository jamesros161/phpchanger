#!/usr/bin/python2.7

from inputargs import Parser
from api import API
from Log import Logger

logger = Logger()

parser = Parser()
args = parser.argparser.parse_args()
api = API(args)


def main():

    if args.verbose:
        logger.setlevel('INFO')
        logger.log('info', 'Verbose Option Enabled')
        logger.log('warning', 'Verbose Option Enabled')
        logger.log('error', 'Verbose Option Enabled')
        logger.log('critical', 'Verbose Option Enabled')
    if args.debug:
        logger.setlevel('DEBUG')
        logger.log('debug', 'Debug Option Enabled')
        logger.log('info', 'Debug Option Enabled')
        logger.log('warning', 'Debug Option Enabled')
        logger.log('error', 'Debug Option Enabled')
        logger.log('critical', 'Debug Option Enabled')
    if args.quiet:
        logger.setlevel('ERROR')
        logger.log('error', 'Quit Option Enabled')
        logger.log('critical', 'Quit Option Enabled')
    
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
