import os
import sys
import yaml
import requests
from urllib.parse import urljoin


class API(object):
    api_map = {
        'api_org_list': 'api/v1/orgs/orgs/',
        'api_org_detail': 'api/v1/orgs/orgs/{org_id}/',
        'api_users_detail': 'api/v1/users/users/'
    }

    def __getattr__(self, item):
        path = self.api_map[item]
        server = '{}:{}'.format(config.server_url, config.server_port)
        url = urljoin(server, path)
        return url


jumpserver_api = API()


class Interactor(object):

    def __init__(self):
        pass

    def send(self, msg):
        print('\n')
        print(msg)

    def receive(self, prompt):
        print('\n')
        opt = input(prompt)
        return opt

    def send_to_user_error(self, msg):
        self.send('[ERROR] {}'.format(msg))

    def send_to_user_info(self, msg):
        self.send('[INFO] {}'.format(msg))

    def send_to_user_debug(self, msg):
        self.send('[DEBUG] {}'.format(msg))

    def send_to_user_the_script_description(self):
        description = '''
        Welcome to the automatic creation of asset permissions script:\n
        
        The script flow is as follows:\n
        1. Enter the name of the organization\n
        2. Enter the user's username\n
        3. Enter the username of the system user\n
        4. Enter the asset's hostname or enter assets CSV file path\n
        5. Create asset permission\n
        
        '''
        self.send(description)

    def ask_user_if_next_step(self):
        opt = self.receive('Go on (Y/N): ')
        if opt in ['N', 'n']:
            self.send('Exit')
            sys.exit(0)

    def ask_user_for_org_name(self):
        opt = self.receive('Input Organization name: ')
        return opt

    def ask_user_for_user_username(self):
        opt = self.receive("Input user's username: ")
        return opt

    def ask_user_if_continue_add(self, resource):
        opt = self.receive("Continue to add {}? (Y/N): ".format(resource))
        if opt in ['N', 'n']:
            return False
        else:
            return True


interactor = Interactor()


class Logger(object):

    def __init__(self):
        self.writer = self.__create_writer()

    def __create_writer(self):
        f = open('./execute.log', 'ab')
        return f

    def write(self):
        pass


logger = Logger()


class Config(object):

    def __init__(self, file_path):
        self.config = self.get_config_from_file(file_path)
        self.server_url = self.config['server']['url']
        if self.server_url.endswith('/'):
            self.server_url = self.server_url[:-1]
        self.server_port = self.config['server']['port']
        self.authentication_type = self.config['authentication']['type']
        self.authentication_user_username = self.config['authentication']['user']['username']
        self.authentication_user_password = self.config['authentication']['user']['password']
        self.authentication_token = self.config['authentication']['token']['token']
        self.authentication_api_key = self.config['authentication']['api_key']['api_key']
        self.permissions_name_prefix = self.config['permissions']['name_prefix']

    def get_config_from_file(self, file_path):
        if not file_path.endswith('.yml'):
            interactor.send('config file format error: {}'.format(file_path))
            sys.exit(0)
        if not os.path.isfile(file_path):
            interactor.send('config file is not file: {}'.format(file_path))
            sys.exit(0)
        f = open(file_path, 'rb')
        conf = yaml.safe_load(f)
        return conf

    def check(self):
        pass


class Requester(object):

    def __init__(self):
        self.headers = {}
        self.init_headers()

    def init_headers(self):
        self.headers.update({
            'Authorization': 'Bearer 940fa8a5570a462a8818bcaed45d069c',
            'Content-Type': 'application/json'
        })

    def init_headers_jumpserver_org(self, org_name=None, org_id=None):
        self.headers.update({
            'X-JMS-ORG': org_name
        })

    def get(self, url, params=None):
        res = requests.get(url, params, headers=self.headers)
        return res

    def post(self, url, data=None):
        pass


requester = Requester()


class Executor(object):

    def __init__(self):
        self.org_list = []
        self.org_name_list = []
        self.org_name = None
        self.org = {}

        self.users_username = []
        self.users = []

        self.system_users_username = []
        self.assets_hostname = []

    def get_org_list(self):
        url = jumpserver_api.api_org_list
        interactor.send_to_user_debug('Request url: {}'.format(url))
        res = requester.get(url)
        return res.json()

    def check_org_name_exist(self, org_name):
        org_list = self.get_org_list()
        for org in org_list:
            if org['name'] == org_name:
                return True, org
        return False, None

    def wait_and_check_for_user_input_org_name(self):
        while True:
            org_name = interactor.ask_user_for_org_name()
            if org_name.lower() == 'default':
                self.org_name = org_name.upper()
                self.org = {'name': self.org_name}
                break

            exist, org = self.check_org_name_exist(org_name)
            if exist:
                self.org_name = org_name
                self.org = org
                interactor.send_to_user_info('Organization exist: {}'.format(self.org_name))
                break
            interactor.send_to_user_error('Organization not exist: {}'.format(self.org_name))

    def check_user_username_exist(self, username):
        url = jumpserver_api.api_users_detail
        params = {
            'username': username
        }
        res = requester.get(url, params=params)
        if res.status_code == 200:
            users = res.json()
            if len(users) == 1:
                return True, users[0]
            else:
                interactor.send_to_user_error('Exist many to for username: {}'.format(username))
                return False, None
        else:
            return False, None

    def wait_and_check_for_user_input_users_username(self):
        while True:
            interactor.send_to_user_info('Current select users: {}'.format(self.users_username))
            user_username = interactor.ask_user_for_user_username()
            exist, user = self.check_user_username_exist(user_username)
            if exist:
                interactor.send_to_user_info('User exist: {}'.format(user_username))
                if user_username not in self.users_username:
                    self.users_username.append(user_username)
                    self.users.append(user)
                if interactor.ask_user_if_continue_add('user'):
                    continue
                else:
                    break
            else:
                interactor.send_to_user_error('User not exist: {}'.format(user_username))
                if len(self.users) >= 1:
                    if interactor.ask_user_if_continue_add('user'):
                        continue
                    else:
                        break

    def wait_for_user_input_system_users_username(self):
        pass

    def wait_for_user_input_assets_hostname(self):
        pass

    def show_data_of_create_permission(self):
        pass

    def show_data_for_create_permission_result(self):
        pass

    def ask_user_if_continue_create_permission(self):
        pass

    def show_summary_for_the_execute(self):
        pass

    def execute(self):
        self.wait_and_check_for_user_input_org_name()
        requester.init_headers_jumpserver_org(self.org_name)
        self.wait_and_check_for_user_input_users_username()
        self.wait_for_user_input_system_users_username()
        self.wait_for_user_input_assets_hostname()
        self.show_data_of_create_permission()
        interactor.ask_user_if_next_step()
        self.show_data_for_create_permission_result()
        self.ask_user_if_continue_create_permission()
        self.show_summary_for_the_execute()


if __name__ == '__main__':
    config_file_path = '../config_example.yml'

    args = sys.argv
    if len(args) >= 2:
        config_file_path = args[1]

    config = Config(file_path=config_file_path)
    config.check()

    interactor.send_to_user_the_script_description()
    interactor.ask_user_if_next_step()

    executor = Executor()
    executor.execute()
