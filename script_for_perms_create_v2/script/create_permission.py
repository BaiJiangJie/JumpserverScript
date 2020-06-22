"""
create_permission.py - 快速创建 JumpServer 资产授权规则

执行方式：
python create_permission.py config.yml
"""

import sys


class Config:
    """ 配置类 - 包含脚本所需的所有配置选项 """
    pass


def before_creation():
    pass


def create():
    pass


def after_creation():
    pass


def init_config(file_path):
    """ 初始化配置

    :param file_path: 配置文件路径
    :return: Config实例
    """
    config = Config()
    return config


def get_config_file_path():
    """ 获取/校验 配置文件路径 """
    args = sys.argv
    if len(args) >= 2:
        config_file_path = args[1]
    else:
        config_file_path = '../config_example.yml'
    return config_file_path


def main():
    """ 程序入口

    使命:
    * 获取配置文件
    * 初始化配置
    * 创建资产授权规则前的校验
    * 进入创建资产授权规则流程
    *
    """

    config_file_path = get_config_file_path()

    config = init_config(config_file_path)

    before_creation()

    create()

    after_creation()


if __name__ == '__main__':
    main()
