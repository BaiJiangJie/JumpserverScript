# -*- coding: utf-8 -*-

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
import datetime
import requests
from urllib.parse import urljoin
from httpsig.requests_auth import HTTPSignatureAuth


class Config:
    """ 配置类 - 包含脚本所需的所有配置选项 """

    def __init__(self, config_dict):
        # server
        self.server = config_dict['server']

        # authentication
        self.authentication_type = config_dict['authentication']['type']
        self.authentication_api_key_access_key_id = config_dict['authentication']['api_key']['access_key_id']
        self.authentication_api_key_access_key_secret = config_dict['authentication']['api_key']['access_key_secret']

        # log
        self.log_file_path = config_dict['log']['file_path']


class ServerProxy:
    """ 服务代理者- 负责与JumpServer进行交互 """

    def __init__(self):
        self.http_signature_auth = self.generate_http_signature_auth()
        self.org = None

    def set_org(self, org):
        self.org = org

    def get_org_name(self):
        return self.org['name']

    def get_org_id(self):
        return self.org['id']

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
        org_id = self.get_org_id()
        return {
            'X-JMS-ORG': org_id,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Date': "Mon, 17 Feb 2014 06:11:05 GMT"
        }

    def get(self, url, params=None, **kwargs):
        return requests.get(url, params=params, **kwargs)

    def post(self, url, data=None, **kwargs):
        json_data = json.dumps(data)
        return requests.post(url, json_data, **kwargs)

    def request(self, method, url, data=None, params=None, **kwargs):
        assert method in ['get', 'post'], \
            'method `{}` not allowed, must is `get` or `post`'.format(method)

        kwargs['headers'] = self.generate_headers()
        kwargs['auth'] = self.http_signature_auth

        logger.info('向服务端发送请求')
        logger.info('url: {}'.format(url))
        for k, v in kwargs.items():
            logger.info('{}: {}'.format(k, v))

        if method == 'get':
            logger.info('params: {}'.format(params))
            return self.get(url, params=params, **kwargs)

        if method == 'post':
            logger.info('data: {}'.format(data))
            return self.post(url, data=data, **kwargs)

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
            logger.info('User username: {}'.format(username))
            logger.info('Get data form server: {}'.format(users))
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
        res = self.request('get', url, params=params)
        if res.status_code == 200:
            assets = res.json()
            if len(assets) == 1:
                return assets[0]
        return None

    def create_asset_permission(self, data):
        url = self.generate_url('/api/v1/perms/asset-permissions/')
        res = self.request('post', url, data=data)
        if res.status_code in [200, 201]:
            permission = res.json()
            return permission
        else:
            client_proxy.print_error(res.reason)
            client_proxy.print_error(res.content)
            return None

    def test_connectivity(self):
        logger.info('测试服务可连接性')
        self.set_org({'name': 'DEFAULT', 'id': ''})
        url = self.generate_url('/api/health/')
        res = self.request('get', url)
        if res.status_code == 200:
            logger.info('测试服务可连接性...成功')
            return True, None
        else:
            logger.error(res.content)
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
                continue

            if not opt.endswith('.csv'):
                msg = '`{}` format is not `.csv`'
                self.print_error(msg)
                continue
            break
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
        msg = '''欢迎使用 JumpServer 资产授权规则创建脚本 '''
        self.print_info(msg)

    def print_asset_permission_data_display(self, data):
        msg = '''即将使用下面的数据创建授权规则:
        
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

    def print_asset_permissions_created_display(self, permissions_created):
        client_proxy.print_info('本次脚本执行创建授的权规则详细信息如下: ')
        for index, permission in enumerate(permissions_created):
            json_data = json.dumps(permission, indent=4)
            client_proxy.print('{} {} {}'.format('-'*30, index, '-'*30))
            client_proxy.print(json_data)

        permissions_name = [permission['name'] for permission in permissions_created]

        msg = '''本次脚本执行创建的授权规则汇总信息如下如下:
        
        总数: {}
        资产授权规则: {}
        
        '''.format(len(permissions_created), permissions_name)
        client_proxy.print(msg)

    def quit(self, msg=None):
        if msg:
            self.print_info(msg)
        self.print_info('Quit')
        sys.exit(0)


class Logger:
    def __init__(self):
        self.file = open(config.log_file_path, 'a')

    def write(self, msg):
        self.file.write('{} \n'.format(msg))

    def info(self, msg):
        self.write('[INFO] {}'.format(msg))

    def debug(self, msg):
        self.write('[DEBUG] {}'.format(msg))

    def error(self, msg):
        self.write('[ERROR] {}'.format(msg))

    def __delete__(self, instance):
        instance.file.close()


def before_creation():
    """ 执行创建前的准备工作

    * 测试配置服务端的可连接性
    * 展示脚本的描述信息

    :return: None
    """
    # test server connectivity
    client_proxy.print_info('测试服务连接性...')
    success, msg = server_proxy.test_connectivity()
    if not success:
        client_proxy.quit('服务连接性测试...失败: {}'.format(msg))
    else:
        client_proxy.print_info('测试服务连接性...成功')

    # print script description
    client_proxy.print_script_description()


class AssetPermissionDataOperator:
    """
    对用户输入的数据以及从服务端获取回来的数据进行方便存取
    """

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
    """ 创建授权规则

    * 获取用户输入组织名称
    * 获取用户输入资产授权规则名称
    * 获取用户输入用户的用户名
    * 获取用户输入用户的系统用户名称
    * 获取用户输入资产的数据来源 (csv/手动输入)
        - 获取用户输入csv文件路径
        - 获取用户输入资产的主机名称
    * 展示即将待创建使用的数据
    * 等待用户确认创建
    * 执行创建

    :return: 创建成功的资产授权规则信息, dict
    """

    data_operator = AssetPermissionDataOperator()

    # org
    while True:
        org_name = client_proxy.input_org_name()
        if org_name.upper() == 'DEFAULT':
            org = {'name': org_name.upper(), 'id': ''}
        else:
            org = server_proxy.get_org(org_name)
            if org is None:
                client_proxy.print_error('组织 `{}` 不存在'.format(org_name))
                continue
        data_operator.set_org(org)
        server_proxy.set_org(org)
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
        while True:
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
                else:
                    assets.append(asset)
            if len(assets) == 0:
                client_proxy.print_info('没有有效资产')
                continue
            else:
                break
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
    else:
        permission = None
        client_proxy.print_info('取消创建授权规则')

    return permission


def after_creation(permissions_created):
    """
    :param permissions_created: 本次脚本执行创建的授权规则
    :return:
    """
    client_proxy.print_asset_permissions_created_display(permissions_created)


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


def init_logger():
    """ 初始化日志记录者"""
    return Logger()


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

    功能:
    *
    * 执行创建前的准备工作
    * 创建
    * 执行创建后的收尾工作
    *
    """
    permissions_created = []

    before_creation()

    if not client_proxy.input_if_continue():
        client_proxy.quit()

    while True:
        permission = create()

        if permission is not None:
            permissions_created.append(permission)

        if client_proxy.input_if_continue():
            continue

        break

    after_creation(permissions_created)


if __name__ == '__main__':
    """
    * 初始化客户端代理者
    * 初始化配置
    * 初始化服务代理者
    * 初始化日志记录者
    * 进入主程序
    """
    client_proxy = init_client_proxy()
    config = init_config()
    server_proxy = init_server_proxy()
    logger = init_logger()

    logger.info('-'*50)
    logger.info('时间: {}'.format(datetime.datetime.now()))

    main()
