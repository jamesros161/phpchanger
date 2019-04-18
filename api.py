import json, sys, os, warnings, tempfile, urllib
from getpass import getuser
from subprocess import Popen, PIPE, call

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

    def check_api_return_for_issues(self, api_return, cmd_type):
        if cmd_type == "whmapi1":
            #print(cmd_type)
            # kill the script if these
            #print(api_return['metadata']['reason'])
            if api_return['metadata']['version'] != 1:
                sys.exit("This script not tested with whmapi version " +  api_return['metadata']['version'] + "expected 1 instead, exiting.")
            #print(api_return['metadata']['result'])
            if api_return['metadata']['result'] != 1:
                sys.exit("whmapi1 returned error flag with this reason, exiting:\n" + api_return['metadata']['reason'])
        elif cmd_type == "uapi":
            #print(cmd_type)
            # kill the script if these
            #print(api_return['apiversion'])
            if api_return['apiversion'] != 3:
                sys.exit("This script not tested with uapi version " + api_return['apiversion'] + "expected 3 instead, exiting.")
            #print(api_return['result']['errors'])
            if api_return['result']['errors'] is not None:    
                sys.exit("uapi returned this error, exiting:\n" + '\n'.join(error for error in api_return['result']['errors']))

            # warn the user if these
            #print(api_return['result']['messages'])
            if api_return['result']['messages'] is not None:
                print(api_return['result']['messages'])
                warnings.warn("uapi returned this message:\n" + '\n'.join(message for message in api_return['result']['messages']))
            #print(api_return['result']['warnings'])
            if api_return['result']['warnings'] is not None:
                print(api_return['result']['warnings'])
                warnings.warn("uapi returned this warning:\n" + '\n'.join(warning for warning in api_return['result']['warnings']))
        else:
            print("Unrecognized cmd_type, can't check.")

    def call(self, api,cmd='',params=[],module=None, user=''):
        if api == 'whmapi1' and self.current_user != 'root':
            sys.exit('WHMAPI1 commands must be run as root.')
        if api == 'whmapi1' and self.current_user == 'root':
            popenargs = [api, cmd, '--output=json'] + params
        if api == 'uapi' and self.current_user == 'root':
            popenargs = [api, '--user=' + user, module, cmd, '--output=json'] + params
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
            self.check_api_return_for_issues(data, api)
            return(data)
        else:
            sys.exit(api + ' Command Failed to Run')

    def get_installed_php_versions(self):
        uapi_installed_php_versions = self.call("uapi", module="LangPHP", cmd="php_get_installed_versions")

        return uapi_installed_php_versions['result']['data']['versions']

    def breakup_domains_by_users(self):
        
        users_domains = {}
        i = 0
        while i < len(self.args.domains):
            domain = self.args.domains[i]
            user = self.call('whmapi1', cmd='getdomainowner',params=['domain=' + domain])['data']['user']
            if user is not None:
                users_domains[domain] = user
            else:
                print("\n" + domain + " Either does not exist, " 
                    "or is not owned by the user calling this function --skipping\n"
                    )
            i += 1

        return users_domains
    
    def current_user_owns_this_domain(self, domain):
        users_domains = []
        response = self.call('uapi', module='DomainInfo', 
            cmd='list_domains', user=self.current_user)
        data = response['result']['data']
        users_domains = [data['main_domain']]
        users_domains = users_domains + data['sub_domains']
        users_domains = users_domains + data['addon_domains']
        users_domains = users_domains + data['parked_domains']
        if domain in users_domains:
            return True
        else:
            return False
        
    def manager_get(self):
        api = "uapi"
        module = "LangPHP"
        cmd = "php_get_vhost_versions"

        users_domains = self.breakup_domains_by_users()
        for domain , user in users_domains.iteritems():
            vhost_php_versions = self.call(api, user=user, cmd=cmd, module=module)
            for vhost in vhost_php_versions['result']['data']:
                if vhost['vhost'] == domain:          
                    print '\nVHOST: ' + vhost['vhost'] + ":"
                    if "system_default" in vhost['phpversion_source']:
                        print "PHP Version: inherit (" + vhost['version'] + ")"
                    else:
                        print "PHP Version: " + vhost['version']
                    print "PHP-FPM Status: " + ("Enabled" if vhost['php_fpm'] == 1 else "Disabled")
                    if vhost['php_fpm'] == 1:
                        print("PHP-FPM Pool, Max Children: " + str(vhost['php_fpm_pool_parms']['pm_max_children']))
                        print("PHP-FPM Pool, Process Idle Timeout: " + str(vhost['php_fpm_pool_parms']['pm_process_idle_timeout']))
                        print("PHP-FPM Pool, Max Requests: " + str(vhost['php_fpm_pool_parms']['pm_max_requests']) + "\n")
                
    def manager_set(self):
        if self.current_user == "root":
            api = "whmapi1"
            cmd = "php_set_vhost_versions"
            params = []

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

            self.call(api, cmd=cmd, params=params)
            print('The PHP version for the selected domains has been set to ' + php_id)

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
            #print(params)
            self.call(api, module=module, cmd=cmd, params=params)
            print('The PHP version for the selected domains has been set to ' + php_id)
    
    def ini_getter(self,user,domain):
        params = ['type=vhost', 'vhost=' + domain]
        php_ini_settings = self.call('uapi', 
            user=user, module='LangPHP', 
            cmd='php_ini_get_user_content', params=params)
        metadata = php_ini_settings['result']['metadata']['LangPHP']
        print(metadata['vhost'] + " (" + metadata['path'] + "):\n")
        print(unescape(php_ini_settings['result']['data']['content']))
    
    def ini_setter(self,user,domain):
        params = ['type=vhost', 'vhost=' + domain]
        for index, setting in enumerate(self.args.setting, start=1):
            params.append("directive-" + str(index) + "=" + setting[0] + "%3A" + setting[1])
        print (self.call('uapi', user=user, 
            module='LangPHP', cmd='php_ini_set_user_basic_directives', 
            params=params))

    def ini_get(self):
        user_domains = self.breakup_domains_by_users()
        for key, value in user_domains.iteritems():
            if self.current_user == 'root':
                self.ini_getter(value, key)
            else:
                x = 0
                while x < len(key):
                    if self.current_user_owns_this_domain(key[x]):
                        self.ini_getter(self.current_user, key[x])
                    else:
                        print('\nDomain ' + value[x] + ' is not owned by this user --skipping...\n')
                    x += 1

    def ini_set(self):
        user_domains = self.breakup_domains_by_users()
        for key, value in user_domains.iteritems():
            if self.current_user == 'root':
                self.ini_setter(value, key)
            else:
                x = 0
                while x < len(value):
                    if self.current_user_owns_this_domain(key[x]):
                        self.ini_setter(self.current_user, key[x])
                    else:
                        print('\nDomain ' + value[x] + ' is not owned by this user --skipping...\n')
                    x += 1
    
    def ini_editor(self, user, domain):
        params = ['type=vhost', 'vhost=' + domain]
        php_ini_settings = self.call('uapi', user=user, module='LangPHP', cmd='php_ini_get_user_content', params=params)
        contents_to_edit = tempfile.NamedTemporaryFile(suffix=".tmp")
        contents_to_edit.write(unescape(php_ini_settings['result']['data']['content']))
        contents_to_edit.flush()
        call([os.environ.get('EDITOR', 'nano'), contents_to_edit.name])
        contents_to_edit.seek(0)
        uri_encoded_contents = urllib.quote(contents_to_edit.read(), safe='')
        setparams = params
        setparams.append('content=' + uri_encoded_contents)
        new_php_ini_settings = self.call('uapi', user=user, module='LangPHP', cmd='php_ini_set_user_content', params=setparams)
        print(new_php_ini_settings)

    def ini_edit(self):
        user_domains = self.breakup_domains_by_users()
        for key, value in user_domains.iteritems():
            if self.current_user == 'root':
                self.ini_editor(value, key)
            else:
                x = 0
                while x < len(key):
                    if self.current_user_owns_this_domain(key[x]):
                        self.ini_editor(self.current_user, value[x])
                

    