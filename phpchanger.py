#!/usr/bin/python2.7
'''cPanels EasyApache 4 MultiPHP tools, terminal edition.'''
import sys
import os
import warnings
from getpass import getuser
from subprocess import Popen, PIPE, call
from inputargs import Parser
import tempfile
import urllib

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


def main():
    determine_uapi_access()

    print(args)

    # start the selected module code
    # args.func()


def determine_uapi_access():
    '''this program needs to run uapi commands differently if ran as user, or as root, and needs to exit if ran as anything else (like a non-cPanel linux user)'''
    global CURRENT_USER
    CURRENT_USER = getuser()

    if CURRENT_USER != "root":
        # this testing command is kinda arbitrary, but list_features is a decent one to use since it should work on any real cPanel user
        testing_cmd = 'uapi Features list_features > /dev/null'
        testing_stderr = Popen(
            testing_cmd, 
            stdout=PIPE, 
            stderr=PIPE,
            ).communicate()
        if args['verbose']:
            print('UAPI Access Test STDOUT: ' + str(testing_cmd[0]))
            print('UAPI Access Test STDERR: ' + str(testing_cmd[1]))
            
        if "Failed to load cPanel user file for" in testing_stderr:
            sys.exit("This needs to be ran as either root, or as the cPanel user you wish to modify.")
    else:
        testing_cmd = ['uapi', 'Features list_features']
        testing_stderr = Popen(
            testing_cmd, 
            stdout=PIPE, 
            stderr=PIPE,
            ).communicate()
        if args['verbose']:
            print('UAPI Access Test STDOUT: ' + str(testing_cmd[0]))
            print('UAPI Access Test STDERR: ' + str(testing_cmd[1]))
            
        

"""
def check_api_return_for_issues(api_return, cmd_type):
    '''This checks the return values of uapi to exit or warn the user if uapi is telling us something has gone wrong'''

    if cmd_type == "whmapi":
        # kill the script if these
        if api_return['metadata']['version'] != 1:
            sys.exit("This script not tested with whmapi version " +  api_return['metadata']['version'] + "expected 1 instead, exiting.")
        if api_return['metadata']['result'] != 1:
            sys.exit("whmapi1 returned error flag with this reason, exiting:\n" + api_return['metadata']['reason'])
    elif cmd_type == "uapi":
        # kill the script if these
        if api_return['apiversion'] != 3:
            sys.exit("This script not tested with uapi version " + api_return['apiversion'] + "expected 3 instead, exiting.")
        if api_return['result']['errors'] is not None:
            sys.exit("uapi returned this error, exiting:\n" + '\n'.join(error for error in api_return['result']['errors']))

        # warn the user if these
        if api_return['result']['messages'] is not None:
            warnings.warn("uapi returned this message:\n" + '\n'.join(message for message in api_return['result']['messages']))
        if api_return['result']['warnings'] is not None:
            warnings.warn("uapi returned this warning:\n" + '\n'.join(warning for warning in api_return['result']['warnings']))
    else:
        print("Unrecognized cmd_type, can't check.")

def run_cmd_and_parse_its_yaml_return(cmd):
    if args.verbose:
        print "+ " + cmd
    response = []
    response[0], response[1] = Popen(
        cmd, stdout=PIPE, 
        stderr=PIPE
        ).communicate()
    return response

def get_user_arg(user):
    if user == getuser():
        return ""
    else:
        return " --user=" + user

def breakup_domains_by_users(domains_to_check):
    '''build list from domains into list of matching users, and their matching domains'''
    if CURRENT_USER == "root":
        whmapi_domain_info = run_cmd_and_parse_its_yaml_return("whmapi1 get_domain_info")

        matching_domain_info = [domain_info for domain_info in whmapi_domain_info['data']['domains'] if domain_info['domain'] in domains_to_check]

        matching_users = {domain_info["user"] for domain_info in matching_domain_info}

        # transform list of matching domain info into dict of matching users and their own matching domains

        return [
            {
                "user": this_user,
                "domains": [domain_info["domain"] for domain_info in matching_domain_info if domain_info["user"] == this_user]
            } for this_user in matching_users
        ]

    else:
        return [
            {
                "user": CURRENT_USER,
                "domains": domains_to_check
            }
        ]

def manager():
    def get_installed_php_versions(user_arg):
        uapi_installed_php_versions = run_cmd_and_parse_its_yaml_return("uapi LangPHP php_get_installed_versions" + user_arg)
        check_api_return_for_issues(uapi_installed_php_versions, "uapi")

        return uapi_installed_php_versions['result']['data']['versions']

    def manager_get(domains, user_arg):
        cmd_type = "uapi"
        cmd = "uapi LangPHP php_get_vhost_versions" + user_arg

        vhost_php_versions = run_cmd_and_parse_its_yaml_return(cmd)
        check_api_return_for_issues(vhost_php_versions, cmd_type)

        for vhost in (vhost for vhost in vhost_php_versions['result']['data'] if vhost['vhost'] in domains):
            print
            print vhost['vhost'] + ":"
            if "system_default" in vhost['phpversion_source']:
                print "PHP Version: inherit (" + vhost['version'] + ")"
            else:
                print "PHP Version: " + vhost['version']
            print "PHP-FPM Status: " + ("Enabled" if vhost['php_fpm'] == 1 else "Disabled")
            if vhost['php_fpm'] == 1:
                print "PHP-FPM Pool, Max Children: " + str(vhost['php_fpm_pool_parms']['pm_max_children'])
                print "PHP-FPM Pool, Process Idle Timeout: " + str(vhost['php_fpm_pool_parms']['pm_process_idle_timeout'])
                print "PHP-FPM Pool, Max Requests: " + str(vhost['php_fpm_pool_parms']['pm_max_requests'])
    def manager_set(domains, user_arg):
        if CURRENT_USER == "root":
            cmd_type = "whmapi"
            cmd = "whmapi1 php_set_vhost_versions"

            if isinstance(args.fpm, (list,)):
                if args.version is None:
                    warnings.warn('Keep in mind that PHP-FPM will fail to enable if the PHP version is set to "inherit". This script doesnt check for that, hopefully you did.')
                elif args.version == "inherit" :
                    sys.exit('PHP-FPM cannot be enabled while also setting PHP version to "inherit", exiting.')

                cmd += " php_fpm_pool_parms='"
                cmd += '{"pm_max_children":' + args.fpm[0] + ',"pm_process_idle_timeout":' + args.fpm[1] + ',"pm_max_requests":' + args.fpm[2] + '}'
                cmd += "' php_fpm=1"
            elif args.fpm is False:
                cmd += " php_fpm=0"
        else:
            cmd_type = "uapi"
            cmd = "uapi LangPHP php_set_vhost_versions"

            # args.fpm ends up true if neither --fpm, --nofpm are given
            if args.fpm is not True:
                warnings.warn("Adjusting PHP-FPM configuration not possible without root. Skipping that request...")
        if args.version:
            installed_php_versions = get_installed_php_versions(user_arg)

            # if user gave us digits, prefix ea-php, else we assume the user gave a full php ID.
            try:
                php_id = "ea-php" + str(int(args.version))
            except ValueError:
                php_id = args.version

            if php_id in installed_php_versions or php_id == "inherit":
                cmd += " version=" + php_id
            else:
                sys.exit("Provided PHP version " + php_id + " is not installed. Currently installed:\n" + '\n'.join(installed_php_versions))

        for domain in domains:
            cmd += " vhost=" + domain

        cmd_return = run_cmd_and_parse_its_yaml_return(cmd)
        check_api_return_for_issues(cmd_return, cmd_type)

    users_doms_to_check = breakup_domains_by_users(args.domains)
    for user_doms in users_doms_to_check:
        uapi_user_arg = get_user_arg(user_doms["user"])
        doms_list = user_doms["domains"]

        if args.action == "get":
            manager_get(doms_list, uapi_user_arg)
        elif args.action == "set":
            manager_set(doms_list, uapi_user_arg)

            print "\nSet command for user " + user_doms["user"] + " completed."

            if args.check is True:
                print "Checking with manager get:"
                manager_get(doms_list, uapi_user_arg)

def ini():

    def ini_get(domain, user_arg):
        cmd_type = "uapi"
        cmd = "uapi" + user_arg + " LangPHP php_ini_get_user_content type=vhost vhost=" + domain

        php_ini_settings = run_cmd_and_parse_its_yaml_return(cmd)
        check_api_return_for_issues(php_ini_settings, cmd_type)

        metadata = php_ini_settings['result']['metadata']['LangPHP']

        print(metadata['vhost'] + " (" + metadata['path'] + "):")
        print(unescape(php_ini_settings['result']['data']['content']))
    def ini_set(domain, user_arg):
        cmd_type = "uapi"
        cmd = "uapi" + user_arg + " LangPHP php_ini_set_user_basic_directives type=vhost vhost=" + domain

        for index, setting in enumerate(args.setting, start=1):
            cmd += " directive-" + str(index) + "=" + setting[0] + "%3A" + setting[1]

        cmd_return = run_cmd_and_parse_its_yaml_return(cmd)
        check_api_return_for_issues(cmd_return, cmd_type)
    def ini_edit(domain, user_arg):
        cmd_type = "uapi"
        cmd = "uapi" + user_arg + " LangPHP php_ini_get_user_content type=vhost vhost=" + domain

        php_ini_settings = run_cmd_and_parse_its_yaml_return(cmd)
        check_api_return_for_issues(php_ini_settings, cmd_type)

        contents_to_edit = tempfile.NamedTemporaryFile(suffix=".tmp")
        contents_to_edit.write(unescape(php_ini_settings['result']['data']['content']))
        contents_to_edit.flush()
        call([os.environ.get('EDITOR', 'nano'), contents_to_edit.name])
        contents_to_edit.seek(0)

        uri_encoded_contents = urllib.quote(contents_to_edit.read(), safe='')

        print uri_encoded_contents

        cmd_type = "uapi"
        cmd = "uapi" + user_arg + " LangPHP php_ini_set_user_content type=vhost vhost=" + domain + " content=" + uri_encoded_contents

        php_ini_settings = run_cmd_and_parse_its_yaml_return(cmd)
        check_api_return_for_issues(php_ini_settings, cmd_type)

    users_doms_to_check = breakup_domains_by_users(args.domains)
    for user_doms in users_doms_to_check:
        uapi_user_arg = get_user_arg(user_doms["user"])
        doms_list = user_doms["domains"]
        for domain in doms_list:
            if args.action == "get":
                ini_get(domain, uapi_user_arg)
            elif args.action == "set":
                ini_set(domain, uapi_user_arg)

                print "\nSet command for user " + user_doms["user"] + " completed."

                if args.check is True:
                    print "Checking with ini get:"
                    ini_get(domain, uapi_user_arg)
            elif args.action == "edit":
                ini_edit(domain, uapi_user_arg)
"""

if __name__ == '__main__':
    main()
