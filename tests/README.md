# SAST 控制台测试

本目录包含用于测试SAST控制台API和前端数据的各种测试脚本。

## 目录结构

```
tests/
├── logs/               # 测试日志输出目录
├── run_tests.py        # 主测试运行器
├── test_agents_data.py # 代理数据测试
├── test_dashboard_data.py # 仪表盘数据测试
├── test_vulnerability_data.py # 漏洞数据测试
├── test_console_api.py # 控制台API功能测试
├── load_test_console_api.py # API负载测试
├── verify_all_apis.py  # API验证脚本
├── verify_api.py       # 简单API验证
└── README.md           # 本文件
```

## 使用方法

### 单个测试运行

要运行特定的测试脚本，请使用：

```bash
# 激活虚拟环境
source ../venv/bin/activate

# 运行特定测试
python test_agents_data.py
```

### 运行所有测试

要运行所有测试，请使用主测试脚本：

```bash
# 激活虚拟环境
source ../venv/bin/activate

# 运行所有测试
python run_tests.py
```

### API验证

要快速验证API是否工作正常，可以使用验证脚本：

```bash
# 激活虚拟环境
source ../venv/bin/activate

# 验证API
python verify_all_apis.py

# 或使用简单的验证
python verify_api.py
```

## 测试配置

大多数测试默认连接到本地开发服务器(`http://localhost:3000`)。要测试生产环境，请修改脚本中的`BASE_URL`常量。

## 日志

所有测试日志将保存在`logs`目录下，同时输出到控制台。 