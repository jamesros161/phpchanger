from argparse import ArgumentParser
from argparse import RawTextHelpFormatter as Raw
from api import API

class Parser():
    def __init__(self):
        self.epilogs = Epilogs()
        self.helpstr = HelpStrings()

        self.argparser = ArgumentParser(
            description="cPanels EasyApache 4 MultiPHP tools, terminal edition.",
            prog="multiphp.py",
            epilog=self.epilogs.argparser,
            formatter_class=Raw
        )
        self.argparser.add_argument(
            '--verbose',
            action='store_true',
            help='verbose'
        )

        self.create_parent_parsers()
        self.create_primary_subparsers()
        self.create_mngr_subparsers()
        self.create_ini_subparsers()
        self.api = API(self.argparser.parse_args)
 
    def create_parent_parsers(self):

        self.dom_parser = ArgumentParser(add_help=False)
        self.dom_parser.add_argument('domains',
            type=str.lower,
            help=self.helpstr.dom_parser,
            nargs="+"
        )

        self.check_parser = ArgumentParser(add_help=False)
        self.check_parser.add_argument(
            '-c', '--check',
            help=self.helpstr.check_parser,
            action='store_true'
        )
    
    def create_primary_subparsers(self):
        self.primary_subparser = self.argparser.add_subparsers(
            help=self.helpstr.primary_subparser)
        
        self.mngr_parser = self.primary_subparser.add_parser('manager',
            description="The cPanel MultiPHP Manager, terminal edition.",
            help=self.helpstr.mngr_parser,
            epilog=self.epilogs.mngr_parser,
            formatter_class=Raw
        )

        self.ini_parser = self.primary_subparser.add_parser('ini',
            description="The cPanel MultiPHP INI Editor, terminal edition.",
            help=self.helpstr.ini_parser,
            epilog=self.epilogs.ini_parser,
            formatter_class=Raw
        )

    def create_mngr_subparsers(self):
        self.mngr_subparser = self.mngr_parser.add_subparsers(
            help=self.helpstr.mngr_subparsers
        )

        self.mngr_get_parser = self.mngr_subparser.add_parser( 'get',
            help=self.helpstr.mngr_get_parser,
            parents=[self.dom_parser],
            epilog=self.epilogs.mngr_get_parser,
            formatter_class=Raw
        )
        self.mngr_get_parser.set_defaults(func=self.api.manager_get)


        self.mngr_set_parser = self.mngr_subparser.add_parser( 'set',
            help=self.helpstr.mngr_set_parser,
            parents=[self.dom_parser, self.check_parser],
            epilog=self.epilogs.mngr_set_parser,
            formatter_class=Raw
        )

        self.create_mngr_set_args()
    
    def create_mngr_set_args(self):

        self.mngr_set_parser.add_argument('-v', '--version',
            help=self.helpstr.php_ver_arg,
            type=str,
            metavar="php_version_id"
        )

        self.mngr_set_fpmgroup = \
            self.mngr_set_parser.add_mutually_exclusive_group()
        self.mngr_set_fpmgroup.add_argument(
            '--nofpm',
            help=self.helpstr.nofpm,
            dest='fpm',
            action='store_false'
        )

        self.mngr_set_fpmgroup.add_argument(
            '--fpm',
            help=self.helpstr.fpm,
            default=None,
            metavar=('max_children', 
                'process_idle_timeout', 
                'max_requests'),
            nargs=3
        )
    
    def create_ini_subparsers(self):
        self.ini_subparser = self.ini_parser.add_subparsers(
            help=self.helpstr.ini_subparsers
        )

        self.ini_get_parser = self.ini_subparser.add_parser( 'get',
            help=self.helpstr.ini_get_parser,
            parents=[self.dom_parser],
            epilog=self.epilogs.ini_get_parser,
            formatter_class=Raw
        )

        self.ini_set_parser = self.ini_subparser.add_parser( 'set',
            help=self.helpstr.ini_set_parser,
            parents=[self.dom_parser, self.check_parser],
            epilog=self.epilogs.ini_set_parser,
            formatter_class=Raw
        )

        self.ini_edit_parser = self.ini_subparser.add_parser( 'edit',
            help=self.helpstr.ini_edit_parser,
            parents=[self.dom_parser, self.check_parser],
            epilog=self.epilogs.ini_edit_parser,
            formatter_class=Raw
        )

        self.create_ini_set_args()
    
    def create_ini_set_args(self):
        self.ini_set_parser.add_argument('-s', '--setting',
            help=self.helpstr.ini_set_settings,
            required=True,
            metavar=('php_setting', 'value'),
            nargs=2,
            action='append'
        )

class Epilogs():
    def __init__(self):
        self.argparser = (
            "usage examples:\n"
            "  multiphp.py manager get example.com example2.com\n"
            "  multiphp.py ini edit example.com"
        )
        self.mngr_parser = (
            "usage examples:\n"
            "  multiphp.py manager get example.com \n"
            "  multiphp.py manager set example.com -v 73"
        )

        self.mngr_get_parser = (
            "usage examples:\n"
            "  multiphp.py manager get example.com\n"
            "  multiphp.py manager get example.com "
            "example2.com example3.com"
        )

        self.mngr_set_parser = (
            "usage examples:\n"
            "  multiphp.py manager set example.com -v 73\n"
            "  multiphp.py manager set example.com "
            "example2.com example3.com -v inherit --nofpm\n"
            "  multiphp.py manager set example.com example2.com "
            "--fpm 5 10 20\n"
            "  multiphp.py manager set example.com -v ea-php72"
            " --fpm 50 25 100"
        )

        self.ini_parser = (
            "usage examples:\n"
            "  multiphp.py ini get example.com example2.com\n"
            "  multiphp.py ini set example.com -s memory_limit 128M\n"
            "  multiphp.py ini edit example.com"
        )

        self.ini_get_parser = (
            "usage examples:\n"
            "  multiphp.py ini get example.com\n"
            "  multiphp.py ini get example.com example2.com"
        )
        self.ini_set_parser = (
            "usage examples:\n"
            "  multiphp.py ini set example.com example2.com "
            "-s memory_limit 128M\n"
            "  multiphp.py ini set example.com "
            "-s post_max_size 256M -s upload_max_filesize 256M"
        )

        self.ini_edit_parser = (
            "usage examples:\n"
            "  multiphp.py ini edit example.com\n"
            "  multiphp.py ini edit example.com example2.com"
        )

class HelpStrings():
    def __init__(self):

        self.dom_parser = 'one or more domains to run commands on '            
        
        self.check_parser = 'run get after this command makes changes'

        self.primary_subparser = 'Choose manager or ini'

        self.ini_parser = 'mess with them PHP settings'

        self.ini_subparsers = 'Choose get or set'

        self.ini_set_settings = (
            "set a php setting to a given value, "
            "can be passed multiple times"
        )

        self.ini_get_parser = 'check PHP settings'

        self.ini_set_parser = 'make changes to specified PHP settings'

        self.ini_edit_parser = (
            "make changes with $EDITOR to "
            "current PHP settings config"
        )

        self.mngr_parser = 'mess with them PHP versions'

        self.mngr_subparsers = 'Choose get or set'

        self.mngr_get_parser = 'check PHP versions and PHP-FPM settings'

        self.mngr_set_parser = (
            "make changes to PHP versions "
            "and PHP-FPM settings"
        )

        self.php_ver_arg = (
            "PHP version ID to use,"
            "like ea-php## or alt-php##, or just the two"
            "## digits to imply ea-php##, or the \"inherit\" option"
        )
        
        self.nofpm = 'disable PHP-FPM (requires root)'

        self.fpm = 'enable PHP-FPM, with these pool variables (requires root)'
