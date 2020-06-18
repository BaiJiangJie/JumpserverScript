import sys


class Config(object):

    def __init__(self, file_path):
        self.file_path = file_path
        self.log_file_path = './execute.log'

    def init(self):
        pass


class Logger(object):

    def __init__(self):
        self.file_path = config.log_file_path
        self.writer = self.__create_writer()

    def __create_writer(self):
        f = open(self.file_path, 'a')
        return f

    def write(self):
        pass


class Interactor(object):

    def __init__(self):
        pass

    def send(self, msg):
        pass

    def receive(self):
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
    config = Config()
    logger = Logger()
    requester = Requester()
    interactor = Interactor()
    executor = Executor()
    executor.execute()
