import os
import sys
import yaml
import json


class Interactor(object):

    def __init__(self):
        pass

    def send(self, msg):
        print(msg)

    def send_error(self, msg):
        self.send('[ERROR] {}'.format(msg))

    def send_info(self, msg):
        self.send('[INFO] {}'.format(msg))

    def send_script_description(self):
        pass

    def receive(self, prompt):
        opt = input(prompt)
        return opt

    def ask_next_step(self):
        opt = self.receive('Go on (Y/N): ')
        if opt in ['N', 'n']:
            self.send('Exit')
            sys.exit(0)

    def ask_org_name(self):
        opt = self.receive('Input Organization name: ')
        return opt


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
        conf = yaml.load(f)
        return conf

    def check(self):
        pass


class Requester(object):

    def __init__(self):
        pass

    def get(self):
        pass

    def post(self):
        pass

    def exist(self):
        pass


requester = Requester()


class Executor(object):

    def __init__(self):
        self.org_name = None
        self.user_username = None
        self.system_user_username = None
        self.assets = []

    def check_org_name_exist(self):
        pass

    def get_org_name(self):
        while True:
            self.org_name = interactor.ask_org_name()
            exist = self.check_org_name_exist()
            if exist:
                interactor.send_info('Organization exist: {}'.format(self.org_name))
                break
            interactor.send_error('Organization not exist: {}'.format(self.org_name))

    def get_users_username(self):
        pass

    def get_system_users_username(self):
        pass

    def get_assets_hostname(self):
        pass

    def execute(self):
        self.get_org_name()
        self.get_users_username()
        self.get_system_users_username()
        self.get_assets_hostname()


if __name__ == '__main__':
    config_file_path = '../config_example.yml'

    args = sys.argv
    if len(args) >= 2:
        config_file_path = args[1]

    config = Config(file_path=config_file_path)
    config.check()

    interactor.send_script_description()
    interactor.ask_next_step()

    executor = Executor()
    executor.execute()
