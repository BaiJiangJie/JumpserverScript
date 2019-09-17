# 脚本用来快速创建授权规则

# 注意事项
 - 将 config.yml 配置文件与脚本 script_create_asset_permission_X.py 放至同级目录下
 - 脚本名称中末尾 X 表示脚本的版本号

# 简单使用流程
 - 修改配置文件 
    - 拷贝 (cp config_example.yml config.yml )
    - 修改 (vi config.yml)
 - 执行脚本
   - 方式1
     - 命令：python script_create_asset_permission_X.py
     - 命令执行后会依次提示输入 用户的用户名 和 资产IP
   - 方式2
     - 命令：python script_create_asset_permission_X.py 参数1 参数2
     - 参数1：用户的用户名（eg: x_bai)
     - 参数2: 资产IP（eg: 127.0.0.1）
 - 执行日志记录
   - 由于脚本本身没有做日志记录，执行脚本时可以使用重定向到指定文件，以便需要时查看（只适用于执行脚本方式2）

