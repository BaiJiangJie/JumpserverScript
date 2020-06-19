import os
import sys
import csv
import yaml
import time
import json
import requests
from urllib.parse import urljoin


class API(object):
    api_map = {
        'api_org_list': 'api/v1/orgs/orgs/',
        'api_org_detail': 'api/v1/orgs/orgs/{org_id}/',
        'api_user_list': 'api/v1/users/users/',
        'api_system_user_list': 'api/v1/assets/system-users/',
        'api_asset_list': 'api/v1/assets/assets/',
        'api_asset_permission_list': 'api/v1/perms/asset-permissions/'
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
        3. Enter the name of the system user\n
        4. Enter the asset's hostname or enter assets CSV file path\n
        5. Create asset permission\n
        
        '''
        self.send(description)

    def exit(self):
        self.send_to_user_info('Exit')
        sys.exit(0)

    def ask_user_if_next_step(self):
        opt = self.receive('Go on (Y/N): ')
        if opt in ['N', 'n']:
            return False
        else:
            return True

    def ask_user_for_org_name(self):
        opt = self.receive('Input Organization name: ')
        return opt

    def ask_user_for_user_username(self):
        opt = self.receive("Input user's username: ")
        return opt

    def ask_user_for_system_user_name(self):
        opt = self.receive("Input system user's name: ")
        return opt

    def ask_user_for_assets_data_source(self):
        opt = self.receive("Input asset data source (input/csv): ")
        return opt

    def ask_user_for_assets_csv_file_path(self):
        opt = self.receive("Input csv file path of assets: ")
        return opt

    def ask_user_for_asset_hostname(self):
        opt = self.receive("Input asset's hostname: ")
        return opt

    def ask_user_if_continue_add(self, resource):
        opt = self.receive("Continue to add {}? (Y/N): ".format(resource))
        if opt in ['N', 'n']:
            return False
        else:
            return True

    def ask_user_if_create_permission(self):
        opt = self.receive("Are you sure to create asset permission use the data above? (Y/N):  ")
        if opt in ['N', 'n']:
            return False
        else:
            return True

    def ask_user_if_continue_create_permission(self):
        opt = self.receive("Are you continue create next asset permission? (Y/N):  ")
        if opt in ['N', 'n']:
            return False
        else:
            return True

    def ask_user_if_at_current_org(self, org_name):
        opt = self.receive("Create next asset permission at current org ({})? (Y/N):  ".format(org_name))
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

    def add_jumpserver_org_to_headers(self, org_name=None, org_id=None):
        self.headers.update({
            'X-JMS-ORG': org_id if org_id is not None else org_name
        })

    def get(self, url, params=None):
        res = requests.get(url, params, headers=self.headers)
        return res

    def post(self, url, data=None):
        json_data = json.dumps(data)
        res = requests.post(url, json_data, headers=self.headers)
        return res


requester = Requester()


class Executor(object):

    def __init__(self):
        self.org_list = []
        self.org_name_list = []
        self.org_name = None
        self.org = {}

        self.users_username = []
        self.users = []

        self.system_users_name = []
        self.system_users = []

        self.assets_hostname = []
        self.assets = []

        self.asset_permissions_created = []

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

    def wait_for_user_input_and_check_org_name(self):
        while True:
            org_name = interactor.ask_user_for_org_name()
            if org_name.lower() == 'default':
                org_name = org_name.upper()
                org = {'name': org_name, 'id': None}
                break

            exist, org = self.check_org_name_exist(org_name)
            if exist:
                interactor.send_to_user_info('Organization exist: {}'.format(org_name))
                break

            interactor.send_to_user_error('Organization not exist: {}'.format(org_name))

        self.org_name = org_name
        self.org = org

    def check_user_username_exist(self, username):
        url = jumpserver_api.api_user_list
        params = {
            'username': username
        }
        res = requester.get(url, params=params)
        if res.status_code == 200:
            users = res.json()
            if len(users) == 1:
                return True, users[0]
            else:
                return False, None
        else:
            return False, None

    def wait_for_user_input_and_check_users_username(self):
        users_username = []
        users = []

        while True:
            if len(users_username) >= 1:
                interactor.send_to_user_info('Current select users: {}'.format(users_username))
            user_username = interactor.ask_user_for_user_username()
            exist, user = self.check_user_username_exist(user_username)
            if exist:
                interactor.send_to_user_info('User exist: {}'.format(user_username))
                if user_username not in users_username:
                    users_username.append(user_username)
                    users.append(user)
                if interactor.ask_user_if_continue_add('user'):
                    continue
                else:
                    break
            else:
                interactor.send_to_user_error('User not exist: {}'.format(user_username))
                if len(users) >= 1:
                    if interactor.ask_user_if_continue_add('user'):
                        continue
                    else:
                        break
        self.users_username = users_username
        self.users = users
        interactor.send_to_user_info('Current select users: {}'.format(users_username))

    def check_system_user_name_exist(self, name):
        url = jumpserver_api.api_system_user_list
        params = {
            'name': name
        }
        res = requester.get(url, params=params)
        if res.status_code == 200:
            system_users = res.json()
            if len(system_users) == 1:
                return True, system_users[0]
            else:
                return False, None
        else:
            return False, None

    def wait_for_user_input_and_check_system_users_name(self):
        system_users_name = []
        system_users = []

        while True:
            if len(system_users_name) >= 1:
                interactor.send_to_user_info('Current select system users: {}'.format(system_users_name))
            system_user_name = interactor.ask_user_for_system_user_name()
            exist, system_user = self.check_system_user_name_exist(system_user_name)
            if exist:
                interactor.send_to_user_info('System user exist: {}'.format(system_user_name))
                if system_user_name not in system_users_name:
                    system_users_name.append(system_user_name)
                    system_users.append(system_user)
                if interactor.ask_user_if_continue_add('system user'):
                    continue
                else:
                    break
            else:
                interactor.send_to_user_error('System user not exist: {}'.format(system_user_name))
                if len(system_users) >= 1:
                    if interactor.ask_user_if_continue_add('system user'):
                        continue
                    else:
                        break

        self.system_users_name = system_users_name
        self.system_users = system_users
        interactor.send_to_user_info('Current select system users: {}'.format(system_users_name))

    def check_asset_hostname_exist(self, hostname):
        url = jumpserver_api.api_asset_list
        params = {
            'hostname': hostname
        }
        res = requester.get(url, params=params)
        if res.status_code == 200:
            assets = res.json()
            if len(assets) == 1:
                return True, assets[0]
            else:
                return False, None
        else:
            return False, None

    def check_assets_hostname_exist(self, assets_hostname):
        exist_assets_hostname = []
        exist_assets = []
        not_exist_assets_hostname = []
        not_exist_assets = []

        for hostname in assets_hostname:
            exist, asset = self.check_asset_hostname_exist(hostname)
            if exist:
                exist_assets_hostname.append(hostname)
                exist_assets.append(asset)
            else:
                not_exist_assets_hostname.append(hostname)
                not_exist_assets.append(asset)

        description = '''
        
        Check assets exist result:
        
        Exist assets: {},
        Not exist assets: {}
        
        '''.format(exist_assets_hostname, not_exist_assets_hostname)

        interactor.send(description)
        return exist_assets_hostname, exist_assets

    def get_assets_from_csv(self):
        assets_hostname = []

        while True:
            file_path = interactor.ask_user_for_assets_csv_file_path()
            if not os.path.isfile(file_path) or not file_path.endswith('.csv'):
                interactor.send_to_user_error('{}: is not a valid csv file'.format(file_path))
                continue
            with open(file_path, 'r') as f:
                rows = csv.reader(f)
                for index, row in enumerate(rows):
                    if index == 0:
                        continue
                    if len(row) == 1:
                        assets_hostname.append(row[0])
                break

        exist_assets_hostname, exist_assets = self.check_assets_hostname_exist(assets_hostname)

        description = '''
        
        Get exist assets from csv file `{}` result:
        
        assets: {}
        
        '''.format(file_path, ', '.join(exist_assets_hostname))
        interactor.send(description)

        return exist_assets_hostname, exist_assets

    def get_assets_from_user_input(self):
        assets_hostname = []
        assets = []
        while True:
            if len(assets_hostname) >= 1:
                interactor.send_to_user_info('Current select assets: {}'.format(assets_hostname))
            asset_hostname = interactor.ask_user_for_asset_hostname()
            exist, asset = self.check_asset_hostname_exist(asset_hostname)
            if exist:
                interactor.send_to_user_info('Asset exist: {}'.format(asset_hostname))
                if asset_hostname not in assets_hostname:
                    assets_hostname.append(asset_hostname)
                    assets.append(asset)
                if interactor.ask_user_if_continue_add('asset'):
                    continue
                else:
                    break
            else:
                interactor.send_to_user_info('Asset not exist: {}'.format(asset_hostname))
                if len(assets) >= 1:
                    if interactor.ask_user_if_continue_add('assets'):
                        continue
                    else:
                        break

        description = '''

        Get exist assets from input result:

        assets: {}

        '''.format(', '.join(assets_hostname))
        interactor.send(description)

        return assets_hostname, assets

    def wait_for_user_input_and_check_assets_hostname(self):
        while True:
            source = interactor.ask_user_for_assets_data_source()
            if source == 'csv':
                assets_hostname, assets = self.get_assets_from_csv()
                break
            elif source == 'input':
                assets_hostname, assets = self.get_assets_from_user_input()
                break
            else:
                interactor.send_to_user_info('Input data source option `csv` or `input`')

        self.assets_hostname = assets_hostname
        self.assets = assets
        interactor.send_to_user_info('Current select assets: {}'.format(assets_hostname))

    def get_data_for_create_asset_permission(self):
        name = '{prefix}_{timestamp}'.format(
            prefix=config.permissions_name_prefix,
            timestamp=int(time.time())
        )
        data = {
            'name': name,
            'users_username': self.users_username,
            'users': self.users,
            'system_users_name': self.system_users_name,
            'system_users': self.system_users,
            'assets_hostname': self.assets_hostname,
            'assets': self.assets,
            'org_name': self.org_name,
            'org': self.org
        }
        return data

    def show_data_of_will_create_permission(self, data):
        description = '''
        Asset permission will be created using the following data:
        
        Organization: {org}
        
        Asset permission name: {asset_permission_name}
        
        Users: {users}
        
        System users: {system_users}
        
        Assets: {assets}
        '''
        description = description.format(
            asset_permission_name=data['name'],
            org=data['org_name'],
            users=', '.join(data['users_username']),
            system_users=', '.join(data['system_users_name']),
            assets=', '.join(data['assets_hostname'])
        )
        interactor.send(description)

    def create_asset_permission(self, name=None, users=None, system_users=None, assets=None):
        users_id = [user['id'] for user in users]
        system_users_id = [system_user['id'] for system_user in system_users]
        assets_id = [asset['id'] for asset in assets]

        data = {
            'name': name,
            'users': users_id,
            'system_users': system_users_id,
            'assets': assets_id
        }
        url = jumpserver_api.api_asset_permission_list
        res = requester.post(url, data=data)
        if res.status_code == 200:
            permission = res.json()
            interactor.send_to_user_info('Create asset permission success: {}'.format(json.dumps(permission, indent=4)))
            return True, permission
        else:
            interactor.send_to_user_error('Create asset permission error: {}'.format(res.text))
            return False, None

    def show_data_for_create_permission_result(self, data):
        json_data = json.dumps(data, indent=4)
        interactor.send(json_data)

    def ask_user_if_continue_create_permission(self):
        pass

    def show_summary_for_the_execute(self):
        asset_permissions_name = [
            asset_permission['name'] for asset_permission in self.asset_permissions_created
        ]
        description = '''
        Summary of this script execution is as follows:
        
        Asset permission created count: {}
        
        Asset permissions: {}
        
        '''.format(len(self.asset_permissions_created), ', '.join(asset_permissions_name))
        interactor.send(description)

    def execute(self):
        at_current_org = False
        while True:
            if not at_current_org:
                self.wait_for_user_input_and_check_org_name()
                requester.add_jumpserver_org_to_headers(self.org_name, self.org['id'])

            self.wait_for_user_input_and_check_users_username()
            self.wait_for_user_input_and_check_system_users_name()
            self.wait_for_user_input_and_check_assets_hostname()

            data = self.get_data_for_create_asset_permission()
            self.show_data_of_will_create_permission(data)

            if not interactor.ask_user_if_create_permission():
                interactor.exit()
            success, data = self.create_asset_permission(
                name=data['name'],
                users=data['users'],
                system_users=data['system_users'],
                assets=data['assets']
            )
            self.asset_permissions_created.append(data)
            self.show_data_for_create_permission_result(data)

            continue_create_permission = interactor.ask_user_if_continue_create_permission()
            if continue_create_permission:
                at_current_org = interactor.ask_user_if_at_current_org(self.org_name)
                continue
            else:
                self.show_summary_for_the_execute()
                break


if __name__ == '__main__':
    config_file_path = '../config_example.yml'

    args = sys.argv
    if len(args) >= 2:
        config_file_path = args[1]

    config = Config(file_path=config_file_path)
    config.check()

    interactor.send_to_user_the_script_description()
    if not interactor.ask_user_if_next_step():
        interactor.exit()

    executor = Executor()
    executor.execute()
