### 脚本功能
根据用户输入创建 JumpServer 资产授权规则

### 环境说明
- python 环境
  - python3.x
- 安装依赖包
  - pip install requests drf-httpsig

### 执行前准备
- cp config_example.yml config.yml
- 修改配置文件 config.yml

### 执行脚本
- cd script/
- python main.py config.yml

### 执行过程中需要的资产csv文件内容格式请查看以下文件
- assets_hostname.csv
