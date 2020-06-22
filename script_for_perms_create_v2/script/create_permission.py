"""
create_permission.py - 快速创建 JumpServer 资产授权规则

执行方式：
python create_permission.py config.yml
"""

import sys
import csv
import os
import yaml
import json
import requests
from urllib.parse import urljoin
from httpsig.requests_auth import HTTPSignatureAuth


class Config:
    """ 配置类 - 包含脚本所需的所有配置选项 """

    def __init__(self, config_dict):
        # server
        self.server_url = config_dict['server']['url']
        self.server_port = config_dict['server']['port']
        self.server = '{}:{}'.format(self.server_url, self.server_port)

        # authentication
        self.authentication_type = config_dict['authentication']['type']
        self.authentication_api_key_access_key_id = config_dict['authentication']['api_key']['access_key_id']
        self.authentication_api_key_access_key_secret = config_dict['authentication']['api_key']['access_key_secret']

        # asset permission
        self.asset_permission_name_prefix = config_dict['asset_permission']['name_prefix']


class ServerProxy:
    """ 服务代理者- 负责与JumpServer进行交互 """

    def __init__(self):
        self.http_signature_auth = self.generate_http_signature_auth()
        self._org_name = None

    def set_org_name(self, name):
        self._org_name = name

    def get_org_name(self):
        return self._org_name

    def generate_url(self, path):
        url = urljoin(config.server, path)
        return url

    def generate_http_signature_auth(self):
        signature_headers = ['(request-target)', 'accept', 'date', 'host']
        auth = HTTPSignatureAuth(
            key_id=config.authentication_api_key_access_key_id,
            secret=config.authentication_api_key_access_key_secret,
            headers=signature_headers
        )
        return auth

    def generate_headers(self):
        return {
            'X-JMS-ORG': self.get_org_name(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Date': "Mon, 17 Feb 2014 06:11:05 GMT"
        }

    def get(self, url, params=None, **kwargs):
        return requests.get(url, params=params, **kwargs)

    def post(self, url, data=None, **kwargs):
        json_data = json.dumps(data)
        return requests.post(url, json_data, **kwargs)

    def request(self, method, *args, **kwargs):
        assert method in ['get', 'post'], \
            'method `{}` not allowed, must is `get` or `post`'.format(method)

        kwargs['headers'] = self.generate_headers()
        kwargs['auth'] = self.http_signature_auth

        if method == 'get':
            return self.get(*args, **kwargs)

        if method == 'post':
            return self.post(*args, **kwargs)

    def get_org(self, org_name):
        url = self.generate_url('/api/v1/orgs/orgs/')
        res = self.request('get', url)
        if res.status_code in [200]:
            org_list = res.json()
            for org in org_list:
                if org['name'] == org_name:
                    return org
        return None

    def get_user(self, username):
        url = self.generate_url('/api/v1/users/users/')
        params = {'username': username}
        res = self.request('get', url, params=params)
        if res.status_code == 200:
            users = res.json()
            if len(users) == 1:
                return users[0]
        return None

    def get_system_user(self, name):
        url = self.generate_url('/api/v1/assets/system-users/')
        params = {'name': name}
        res = self.request('get', url, params=params)
        if res.status_code == 200:
            system_users = res.json()
            if len(system_users) == 1:
                return system_users[0]
        return None

    def get_asset(self, hostname):
        url = self.generate_url('/api/v1/assets/assets/')
        params = {'hostname': hostname}
        res = self.request(url, params=params)
        if res.status_code == 200:
            assets = res.json()
            if len(assets) == 1:
                return assets
        return None

    def create_asset_permission(self, data):
        url = self.generate_url('/api/v1/perms/asset-permissions/')
        res = self.request(url, data=data)
        if res.status_code in [200, 201]:
            permission = res.json()
            return permission
        else:
            client_proxy.print_error(res.reason)
            return None

    def test_connectivity(self):
        self.set_org_name('DEFAULT')
        url = self.generate_url('/api/health/')
        res = self.request('get', url)
        if res.status_code == 200:
            return True, None
        else:
            return False, res.reason


class ClientProxy:
    """ 客户端代理者 - 负责与用户行为进行交互"""

    def __init__(self):
        pass

    def input(self, msg):
        opt = input(msg)
        return opt.strip()

    def input_org_name(self):
        opt = self.input('输入组织名称: ')
        return opt

    def input_asset_permission_name(self):
        opt = self.input('输入资产授权规则的名称: ')
        return opt

    def input_user_username(self):
        opt = self.input('输入授权用户的用户名: ')
        return opt

    def input_system_user_name(self):
        opt = self.input('输入授权系统用户的名称: ')
        return opt

    def input_asset_source(self):
        while True:
            opt = self.input("资产数据来源: 1.csv 2.手动输入; -- 请选择: ")
            if opt == '1':
                return 'csv'
            elif opt == '2':
                return 'manual'
            else:
                continue

    def input_asset_source_csv_file_path(self):
        while True:
            opt = self.input('输入授权资产的csv文件路径: ')
            if not os.path.isfile(opt):
                msg = '`{}` is not a file'.format(opt)
                self.print_error(msg)

            if not opt.endswith('.csv'):
                msg = '`{}` format is not `.csv`'
                self.print_error(msg)

            return opt

    def input_asset_hostname(self):
        opt = self.input('输入授权资产的主机名: ')
        return opt

    def input_if_continue(self):
        msg = '继续? (Y/N): '
        opt = self.input(msg)
        if opt.lower() == 'n':
            return False
        else:
            return True

    def print(self, msg):
        print(msg)

    def print_info(self, msg):
        self.print(msg)

    def print_error(self, msg):
        self.print(msg)

    def print_script_description(self):
        msg = ''' 欢迎使用 JumpServer 资产授权规则创建脚本 '''
        self.print_info(msg)

    def print_asset_permission_data_display(self, data):
        msg = ''' 即将使用下面的数据创建授权规则:
        
        名称: {}
        用户: {}
        系统用户: {}
        资产: {}
        '''.format(
            data['name'],
            data['users'],
            data['system_users'],
            data['assets']
        )
        self.print(msg)

    def quit(self, msg=None):
        if msg:
            self.print_info(msg)
        self.print_info('Quit')
        sys.exit(0)


def before_creation():
    client_proxy.print_info('测试服务连接性...')
    success, msg = server_proxy.test_connectivity()
    if not success:
        client_proxy.quit('服务连接性测试...失败: {}'.format(msg))
    else:
        client_proxy.print_info('测试服务连接性...成功')

    client_proxy.print_script_description()


class AssetPermissionDataOperator:

    def __init__(self):
        self.name = ''
        self.users = []
        self.assets = []
        self.system_users = []
        self.org = None

    def get_asset_permission_data(self):
        return {
            'name': self.name,
            'users': self.get_users_id(),
            'system_users': self.get_system_users_id(),
            'assets': self.get_assets_id()
        }

    def get_asset_permission_data_display(self):
        return {
            'org': self.org,
            'name': self.name,
            'users': self.get_users_username(),
            'system_users': self.get_system_users_name(),
            'assets': self.get_assets_hostname()
        }

    def set_name(self, name):
        self.name = name

    # user
    def get_users_username(self):
        return [user['username'] for user in self.users]

    def get_users_id(self):
        return [user['id'] for user in self.users]

    def add_user(self, user):
        users_id = self.get_users_id()
        if user['id'] not in users_id:
            self.users.append(user)

    def add_users(self, users):
        for user in users:
            self.add_user(user)

    # asset
    def get_assets_id(self):
        return [asset['id'] for asset in self.assets]

    def get_assets_hostname(self):
        return [asset['hostname'] for asset in self.assets]

    def add_asset(self, asset):
        assets_id = self.get_assets_id()
        if asset['id'] not in assets_id:
            self.assets.append(asset)

    def add_assets(self, assets):
        for asset in assets:
            self.add_asset(asset)

    # system user
    def get_system_users_id(self):
        return [system_user['id'] for system_user in self.system_users]

    def get_system_users_name(self):
        return [system_user['name'] for system_user in self.system_users]

    def add_system_user(self, system_user):
        system_users_id = self.get_system_users_id()
        if system_user['id'] not in system_users_id:
            self.system_users.append(system_user)

    def add_system_users(self, system_users):
        for system_user in system_users:
            self.add_system_user(system_user)

    # org
    def set_org(self, org):
        self.org = org

    def get_org_name(self):
        return self.org['name']


def create():

    data_operator = AssetPermissionDataOperator()

    # org
    while True:
        org_name = client_proxy.input_org_name()
        if org_name.upper() == 'DEFAULT':
            org = {'name': org_name.upper()}
        else:
            org = server_proxy.get_org(org_name)
            if org is None:
                client_proxy.print_error('组织 `{}` 不存在'.format(org_name))
                continue
        server_proxy.set_org_name(org['name'])
        data_operator.set_org(org)
        break

    # name
    name = client_proxy.input_asset_permission_name()
    data_operator.set_name(name)

    # users
    users = []
    while True:
        user_username = client_proxy.input_user_username()
        user = server_proxy.get_user(user_username)
        if user is None:
            client_proxy.print_error('用户`{}` 不存在'.format(user_username))
            continue
        users.append(user)
        if client_proxy.input_if_continue():
            continue
        data_operator.add_users(users)
        users_username = data_operator.get_users_username()
        client_proxy.print_info('授权的用户列表: {}'.format(users_username))
        break

    # system users
    system_users = []
    while True:
        system_user_name = client_proxy.input_system_user_name()
        system_user = server_proxy.get_system_user(system_user_name)
        if system_user is None:
            client_proxy.print_error('系统用户 `{}` 不存在'.format(system_user_name))
            continue
        system_users.append(system_user)
        if client_proxy.input_if_continue():
            continue
        data_operator.add_system_users(system_users)
        system_users_name = data_operator.get_system_users_name()
        client_proxy.print_info('授权的系统用户列表: {}'.format(system_users_name))
        break

    # assets
    assets = []
    assets_source = client_proxy.input_asset_source()
    if assets_source.lower() == 'csv':
        # read csv file
        csv_file_path = client_proxy.input_asset_source_csv_file_path()
        assets_hostname = []
        with open(csv_file_path, 'r') as f:
            rows = csv.reader(f)
            for index, row in enumerate(rows):
                if index == 0:
                    continue
                if len(row) == 1:
                    assets_hostname.append(row[0])
        # get assets
        for asset_hostname in assets_hostname:
            asset = server_proxy.get_asset(asset_hostname)
            if asset is None:
                client_proxy.print_error('资产 `{}` 不存在'.format(asset_hostname))
            assets.append(asset)
        data_operator.add_assets(assets)
        assets_hostname = data_operator.get_assets_hostname()
        client_proxy.print_info('授权的资产列表: {}'.format(assets_hostname))
    else:
        while True:
            asset_hostname = client_proxy.input_asset_hostname()
            asset = server_proxy.get_asset(asset_hostname)
            if asset is None:
                client_proxy.print_error('资产 `{}` 不存在'.format(asset_hostname))
                continue
            assets.append(asset)
            if client_proxy.input_if_continue():
                continue
            data_operator.add_assets(assets)
            assets_hostname = data_operator.get_assets_hostname()
            client_proxy.print_info('授权的资产列表: {}'.format(assets_hostname))
            break

    # show asset permission data display
    data_display = data_operator.get_asset_permission_data_display()
    client_proxy.print_asset_permission_data_display(data_display)

    # create asset permission
    if client_proxy.input_if_continue():
        data = data_operator.get_asset_permission_data()
        permission = server_proxy.create_asset_permission(data)
        if permission is None:
            client_proxy.print_error('创建授权规则...失败')
        else:
            json_data = json.dumps(permission, indent=4)
            client_proxy.print(json_data)
            client_proxy.print_info('创建资产授权规则...成功')


def after_creation():
    pass


def init_client_proxy():
    """ 初始化客户端代理者
    :return: ClientProxy 实例
    """
    return ClientProxy()


def init_server_proxy():
    """ 初始化服务代理者
    :return: ServerProxy 实例
    """
    return ServerProxy()


def init_config():
    """ 初始化配置
    :return: Config
    """

    args = sys.argv
    if len(args) >= 2:
        config_file_path = args[1]
    else:
        config_file_path = '../config_example.yml'

    if not os.path.isfile(config_file_path):
        msg = '`{}` is not a file'.format(config_file_path)
        client_proxy.quit(msg)

    if not config_file_path.endswith('.yml'):
        msg = '`{}` format is not `.yml`'
        client_proxy.quit(msg)

    with open(config_file_path, 'rb') as f:
        config_dict = yaml.safe_load(f)

    return Config(config_dict)


def main():
    """ 程序入口

    使命:
    *
    * 获取配置文件
    * 初始化配置
    * 初始化服务代理者
    * 初始化客户端代理者
    * 创建前准备工作
    * 进入创建流程
    * 创建后收尾工作
    *
    """
    before_creation()

    if not client_proxy.input_if_continue():
        client_proxy.quit()

    create()

    after_creation()


if __name__ == '__main__':
    client_proxy = init_client_proxy()
    config = init_config()
    server_proxy = init_server_proxy()
    main()
