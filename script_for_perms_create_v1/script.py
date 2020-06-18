import sys
import yaml
import uuid
import requests

USERNAME = None
IP = None
CONFIG = {}


def load_config():
    with open('config.yml') as f:
        data = f.read()
        config = yaml.safe_load(data)
        return config


class HTTP:
    server = None
    token = None

    @classmethod
    def get_default_token(cls):
        token = CONFIG.get('token')
        return token

    @classmethod
    def get_token(cls, username, password):
        token = cls.get_default_token()
        if token:
            print("使用配置文件中的 Token")
            cls.token = token
            return
        print("获取超级管理员 Token")
        data = {'username': username, 'password': password}
        url = "/api/authentication/v1/auth/"
        res = requests.post(cls.server + url, data)
        res_data = res.json()
        token = res_data.get('token')
        print("使用用户名密码获取 Token")
        cls.token = token

    @classmethod
    def get(cls, url, params=None, **kwargs):
        url = cls.server + url
        headers = {
            'Authorization': "Bearer {}".format(cls.token)
        }
        kwargs['headers'] = headers
        res = requests.get(url, params, **kwargs)
        return res

    @classmethod
    def post(cls, url, data=None, json=None, **kwargs):
        url = cls.server + url
        headers = {
            'Authorization': "Bearer {}".format(cls.token)
        }
        kwargs['headers'] = headers
        res = requests.post(url, data, json, **kwargs)
        return res


class User(object):
    def __init__(self):
        self.id = None
        self.username = USERNAME
        self.email_suffix = CONFIG.get('email_suffix')

    def input_preconditions(self):
        if USERNAME:
            self.username = USERNAME
            return
        default_username = CONFIG.get('user_username')
        if default_username:
            self.username = default_username
            return
        self.username = input("Please enter user username: ")

    def get_preconditions(self):
        self.input_preconditions()

    def exist(self):
        print("校验用户")
        url = '/api/users/v1/users/'
        params = {'username': self.username}
        res = HTTP.get(url, params=params)
        res_data = res.json()
        if res.status_code in [200, 201] and res_data:
            self.id = res_data[0].get('id')
            return True
        print("用户不存在: {}".format(self.username))
        return False

    def create(self):
        print("创建用户")
        url = '/api/users/v1/users/'
        data = {
            'name': self.username,
            'username': self.username,
            'email': '{}@{}'.format(self.username, self.email_suffix),
            'is_active': True
        }
        res = HTTP.post(url, data)
        self.id = res.json().get('id')

    def perform(self):
        if not self.username:
            print("用户名不能为空")
            sys.exit()
        if self.exist():
            return
        self.create()


class Node(object):
    def __init__(self):
        self.id = CONFIG.get('node_id')

    def input_preconditions(self):
        manual = CONFIG.get('node_id_manual', False)
        if not manual:
            return
        if self.id is not None:
            return
        self.id = input("Please enter node id: ")

    def get_preconditions(self):
        self.input_preconditions()

    def exist(self):
        print("校验资产节点")
        url = '/api/assets/v1/nodes/{}/'.format(self.id)
        res = HTTP.get(url)
        res_data = res.json()
        if res.status_code in [200, 201] and res_data:
            return True
        print('节点不存在: {}'.format(self.id))
        return False

    def perform(self):
        if self.exist():
            return
        sys.exit()


class AdminUser(object):
    def __init__(self):
        self.id = CONFIG.get('admin_user_id')

    def input_preconditions(self):
        manual = CONFIG.get('admin_user_id_manual', False)
        if not manual:
            return
        if self.id is not None:
            return
        self.id = input("Please enter admin user id: ")

    def get_preconditions(self):
        self.input_preconditions()

    def exist(self):
        print("校验管理用户")
        url = '/api/assets/v1/admin-user/{}/'.format(self.id)
        res = HTTP.get(url)
        res_data = res.json()
        if res.status_code in [200, 201] and res_data:
            return True
        print("管理用户不存在: {}".format(self.id))
        return False

    def perform(self):
        if self.exist():
            return
        sys.exit()


class Asset(object):
    def __init__(self):
        self.id = None
        self.ip = IP
        self.admin_user = AdminUser()
        self.node = Node()

    def input_preconditions(self):
        if IP:
            self.ip = IP
            return
        default_ip = CONFIG.get('asset_ip')
        if default_ip:
            self.ip = default_ip
            return
        self.ip = input("Please enter asset ip: ")

    def get_preconditions(self):
        self.input_preconditions()
        self.admin_user.get_preconditions()
        self.node.get_preconditions()

    def exist(self):
        print("校验资产")
        url = '/api/assets/v1/assets/'
        params = {
            'ip': self.ip
        }
        res = HTTP.get(url, params)
        res_data = res.json()
        if res.status_code in [200, 201] and res_data:
            self.id = res_data[0].get('id')
            return True
        print("资产不存在: {}".format(self.ip))
        return False

    def create(self):
        print("创建资产")
        self.admin_user.perform()
        self.node.perform()
        url = '/api/assets/v1/assets/'
        data = {
            'hostname': self.ip,
            'ip': self.ip,
            'admin_user': self.admin_user.id,
            'nodes': [self.node.id],
            'is_active': True
        }
        res = HTTP.post(url, data)
        self.id = res.json().get('id')

    def perform(self):
        if not self.ip:
            print("资产 IP 不能为空")
            sys.exit()
        if self.exist():
            return
        self.create()


class SystemUser(object):
    def __init__(self):
        self.id = CONFIG.get('system_user_id')

    def input_preconditions(self):
        manual = CONFIG.get('system_user_id_manual', False)
        if not manual:
            return
        if self.id is not None:
            return
        self.id = input("Please enter system user id: ")

    def get_preconditions(self):
        self.input_preconditions()

    def exist(self):
        print("校验系统用户")
        url = '/api/assets/v1/system-user/{}/'.format(self.id)
        res = HTTP.get(url)
        res_data = res.json()
        if res.status_code in [200, 201] and res_data:
            return True
        print("系统用户不存在: {}".format(self.id))
        return False

    def perform(self):
        if self.exist():
            return
        sys.exit()


class AssetPermission(object):

    def __init__(self):
        self.name = None
        self.user = User()
        self.asset = Asset()
        self.system_user = SystemUser()

    def input_preconditions(self):
        manual = CONFIG.get('asset_permission_name_manual', False)
        if not manual:
            return
        self.name = input("Please enter asset permission name: ")

    def get_preconditions(self):
        self.user.get_preconditions()
        self.asset.get_preconditions()
        self.system_user.get_preconditions()
        self.input_preconditions()

    @staticmethod
    def get_name_prefix():
        prefix = CONFIG.get('asset_permission_name_prefix', None)
        return prefix

    def get_name_suffix(self):
        suffix_uuid = str(uuid.uuid4().hex[:6])
        suffix = "{}_{}_{}".format(
            self.user.username, self.asset.ip, suffix_uuid
        )
        return suffix

    def get_name(self):
        if self.name is not None:
            return self.name
        prefix = self.get_name_prefix()
        suffix = self.get_name_suffix()
        if prefix is None:
            name = suffix
        else:
            name = "{}_{}".format(prefix, suffix)
        return name

    def get_actions(self):
        actions = CONFIG.get('asset_permission_actions', ['all'])
        return actions

    def create(self):
        print("创建资产授权规则")
        url = '/api/perms/v1/asset-permissions/'
        name = self.get_name()
        actions = self.get_actions()
        data = {
            'name': name,
            'users': [self.user.id],
            'assets': [self.asset.id],
            'system_users': [self.system_user.id],
            'actions': actions,
            'is_active': True
        }
        print("data: ")
        print(data)
        res = HTTP.post(url, data)
        res_data = res.json()
        if res.status_code in [200, 201]:
            print("response: ")
            print(res_data)
            print("创建资产授权规则成功")
        else:
            print("response: ")
            print(res_data)
            print("创建授权规则失败")

    def perform(self):
        self.user.perform()
        self.asset.perform()
        self.system_user.perform()
        self.create()


class APICreateAssetPermission(object):

    def __init__(self):
        self.jms_url = CONFIG.get('jms_url')
        self.jms_port = CONFIG.get('jms_port')
        self.superuser_username = CONFIG.get('superuser_username')
        self.superuser_password = CONFIG.get('superuser_password')
        self.token = None
        self.server = None
        self.perm = AssetPermission()
        self.get_preconditions()

    def input_preconditions(self):
        if self.jms_url is None:
            self.jms_url = input("Please enter the server url (Jumpserver): ")
        if self.jms_port is None:
            self.jms_port = input("Please enter the server port (80) (Jumpserver): ")
        if self.superuser_username is None:
            self.superuser_username = input("Please enter SuperUser username: ")
        if self.superuser_password is None:
            self.superuser_password = input("Please enter SuperUser password: ")
        self.server = "{}:{}".format(self.jms_url, self.jms_port)

    def get_preconditions(self):
        print("请输入前置条件: ")
        self.input_preconditions()
        self.perm.get_preconditions()

    def init_http(self):
        HTTP.server = self.server
        HTTP.get_token(self.superuser_username, self.superuser_password)

    def perform(self):
        print("执行操作")
        self.init_http()
        self.perm.perform()


if __name__ == '__main__':
    args = sys.argv
    if len(args) >= 2:
        USERNAME = args[1]
    if len(args) >= 3:
        IP = args[2]

    CONFIG = load_config()
    api = APICreateAssetPermission()
    api.perform()
