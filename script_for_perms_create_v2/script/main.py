import os
import sys
import yaml


class Interactor(object):

    def __init__(self):
        pass

    def send(self, msg):
        print(msg)

    def receive(self):
        pass


interactor = Interactor()


class Config(object):

    def __init__(self, file_path):
        self.file_path = file_path
        self.raw = None
        self.log_file_path = None
        self.init()

    def init(self):
        if not self.file_path.endswith('.yml'):
            interactor.send('config file format error: {}'.format(self.file_path))
            sys.exit(0)
        if not os.path.isfile(self.file_path):
            interactor.send('config file is not file: {}'.format(self.file_path))
            sys.exit(0)
        self.raw = yaml.load(self.file_path)


class Logger(object):

    def __init__(self):
        self.file_path = config.log_file_path
        self.writer = self.__create_writer()

    def __create_writer(self):
        f = open(self.file_path, 'a')
        return f

    def write(self):
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


class Executor(object):

    def __init__(self):
        pass

    def execute(self):
        pass


if __name__ == '__main__':
    config_file_path = '../config_example.yml'

    args = sys.argv
    if len(args) >= 2:
        config_file_path = args[1]

    config = Config(file_path=config_file_path)
    logger = Logger()
    requester = Requester()
    executor = Executor()
    executor.execute()
