from getpass import getuser
import sys
from subprocess import Popen, PIPE
import json
from inputargs import Parser

current_user = getuser()
parser = Parser()
args = parser.argparser.parse_args()
print(args)

class API():
    #ef __init__(self):

    def call(self, api,cmd,params,module=None):
        if api == 'whmapi1' and current_user != 'root':
            sys.exit('WHMAPI1 commands must be run as root.')
        if api == 'whmapi1' and current_user == 'root':
            popenargs = [api, cmd, '--output=json'] + params
        if api == 'uapi' and current_user == 'root':
            popenargs = [api, '--user=root', module, cmd, '--output=json'] + params
        if api == 'uapi' and current_user !='root':
            popenargs = [api, module, cmd, '--output=json'] + params
        if api != 'uapi' and api != 'whmapi1':
            sys.exit('invalid api type')
            
        print(popenargs)
        data, error = Popen(popenargs, stdout=PIPE,stderr=PIPE).communicate()
        if error == '':
            data = json.loads(data)
            if params.verbose:
                print('Command Return Data:\n')
                print(data)
            return(data)
        else:
            print('Command Failed to Run')
            sys.exit(error)