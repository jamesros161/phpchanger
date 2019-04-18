import json, sys
from getpass import getuser
from subprocess import Popen, PIPE
import warnings

try:
    from html import unescape  # python 3.4+
except ImportError:
    try:
        from html.parser import HTMLParser  # python 3.x (<3.4)
    except ImportError:
        from HTMLParser import HTMLParser  # python 2.x
    unescape = HTMLParser().unescape

class API():
    def __init__(self, parser_args):
        self.current_user = getuser()
        self.args = parser_args

    def call(self, api,cmd='',params=[],module=None):
        if api == 'whmapi1' and self.current_user != 'root':
            sys.exit('WHMAPI1 commands must be run as root.')
        if api == 'whmapi1' and self.current_user == 'root':
            popenargs = [api, cmd, '--output=json'] + params
        if api == 'uapi' and self.current_user == 'root':
            popenargs = [api, '--user=root', module, cmd, '--output=json'] + params
        if api == 'uapi' and self.current_user !='root':
            popenargs = [api, module, cmd, '--output=json'] + params
        if api != 'uapi' and api != 'whmapi1':
            sys.exit('invalid api type')
            
        data, error = Popen(popenargs, stdout=PIPE,stderr=PIPE).communicate()
        if error == '':
            data = json.loads(data)
            if self.args.verbose:
                print('Command Return Data:\n')
                print(data)
            return(data)
        else:
            print('Command Failed to Run')
            sys.exit(error)

    def get_installed_php_versions(self):
        uapi_installed_php_versions = self.call("uapi", module="LangPHP", cmd="php_get_installed_versions")
        #check_api_return_for_issues(uapi_installed_php_versions, "uapi")

        return uapi_installed_php_versions['result']['data']['versions']

    def breakup_domains_by_users(self):
        domains_to_check = self.args.domains
        '''build list from domains into list of matching users, and their matching domains'''
        if self.current_user == "root":
            whmapi_domain_info = self.call("whmapi1", cmd="get_domain_info")
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
                    "user": self.current_user,
                    "domains": domains_to_check
                }
            ]
    


    def manager_get(self):
        api = "uapi"
        module = "LangPHP"
        cmd = "php_get_vhost_versions"

        vhost_php_versions = self.call(api, cmd, module=module)
        #print vhost_php_versions
        #check_api_return_for_issues(vhost_php_versions, cmd_type)

        for vhost in (vhost for vhost in vhost_php_versions['result']['data'] if vhost['vhost'] in self.args.domains):
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

    def manager_set(self):
        if self.current_user == "root":
            api = "whmapi1"
            cmd = "php_set_vhost_versions"

            if isinstance(self.args.fpm, (list,)):
                if self.args.version is None:
                    warnings.warn('Keep in mind that PHP-FPM will fail to enable if the PHP version is set to "inherit". This script doesnt check for that, hopefully you did.')
                elif self.args.version == "inherit" :
                    sys.exit('PHP-FPM cannot be enabled while also setting PHP version to "inherit", exiting.')
                params=[
                    'php_fpm_pool_parms={"pm_max_children":' + \
                    self.args.fpm[0] + ',"pm_process_idle_timeout":' + \
                    self.args.fpm[1] + ',"pm_max_requests":' + \
                    self.args.fpm[2] + '}',
                    'php_fpm=1'
                ]
            elif self.args.fpm is False:
                params ="php_fpm=0"
            for domain in self.args.domains:
                params.append("vhost=" + domain)
            print(self.call(api, cmd=cmd, params=params))
        else:
            api = "uapi"
            module = "LangPHP"
            cmd = "php_set_vhost_versions"
            params = []

            # args.fpm ends up true if neither --fpm, --nofpm are given
            if self.args.fpm is not True:
                warnings.warn("Adjusting PHP-FPM configuration not possible without root. Skipping that request...")
            if self.args.version:
                installed_php_versions = self.get_installed_php_versions()

            # if user gave us digits, prefix ea-php, else we assume the user gave a full php ID.
            try:
                php_id = "ea-php" + str(int(self.args.version))
            except ValueError:
                php_id = self.args.version

            if php_id in installed_php_versions or php_id == "inherit":
                params.append("version=" + php_id)
            else:
                sys.exit("Provided PHP version " + php_id + " is not installed. Currently installed:\n" + '\n'.join(installed_php_versions))

        for domain in self.args.domains:
            params.append("vhost=" + domain)
        print(params)
        cmd_return = self.call(api, module=module, cmd=cmd, params=params)
        print(cmd_return)
        #check_api_return_for_issues(cmd_return, cmd_type)
    
    def ini_get(self):
        api = "uapi"
        module = "LangPHP"
        cmd = "php_ini_get_user_content"
        domains = self.breakup_domains_by_users()
        print(domains[0]['domains'])
        for domain in domains[0]['domains']:        
            params =['type=vhost', 'vhost=' + domain]
            php_ini_settings = self.call(api, module=module, cmd=cmd, params=params)
            metadata = php_ini_settings['result']['metadata']['LangPHP']
            print(metadata['vhost'] + " (" + metadata['path'] + "):")
            print(unescape(php_ini_settings['result']['data']['content']))