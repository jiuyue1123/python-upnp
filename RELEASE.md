# UPnP 端口映射工具 - 构建和发布指南

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：

- Python 3.7+
- Git
- 网络连接（用于下载依赖）

### 2. 克隆项目

```bash
git clone <your-repo-url>
cd upnp
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 测试 UTF-8 编码

```bash
python test_utf8.py
```

## 📦 本地构建

### Windows 构建

#### 方法 1：使用批处理脚本（推荐）

```cmd
build.bat
```

#### 方法 2：使用 Python 脚本

```cmd
python build.py
```

#### 方法 3：手动构建

```cmd
pip install pyinstaller
pyinstaller --name "upnp-port-mapper-windows" --onefile --windowed --add-data "README.md;." --hidden-import miniupnpc --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.scrolledtext --hidden-import queue --hidden-import threading --hidden-import socket --hidden-import subprocess --hidden-import datetime --hidden-import re --clean upnp_gui.py
```

### Linux 构建

#### 方法 1：使用 Shell 脚本（推荐）

```bash
chmod +x build.sh
./build.sh
```

#### 方法 2：使用 Python 脚本

```bash
python3 build.py
```

#### 方法 3：手动构建

```bash
pip3 install pyinstaller
pyinstaller --name "upnp-port-mapper-linux" --onefile --windowed --add-data "README.md:." --hidden-import miniupnpc --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.scrolledtext --hidden-import queue --hidden-import threading --hidden-import socket --hidden-import subprocess --hidden-import datetime --hidden-import re --clean upnp_gui.py
```

## 🔧 构建配置

### UTF-8 编码支持

所有构建脚本都已配置 UTF-8 编码支持：

- **Windows**: 使用 `chcp 65001` 设置代码页
- **Linux**: 设置 `LANG=C.UTF-8` 环境变量
- **Python**: 配置标准输出编码为 UTF-8

### 构建参数说明

| 参数              | 说明                 |
| ----------------- | -------------------- |
| `--onefile`       | 打包成单个可执行文件 |
| `--windowed`      | 不显示控制台窗口     |
| `--add-data`      | 添加数据文件         |
| `--hidden-import` | 显式导入隐藏模块     |
| `--clean`         | 构建前清理临时文件   |

### 支持的隐藏模块

- `miniupnpc`: UPnP 核心库
- `tkinter`: GUI 框架
- `tkinter.ttk`: 现代化控件
- `tkinter.scrolledtext`: 滚动文本框
- `queue`: 线程间通信
- `threading`: 多线程支持
- `socket`: 网络通信
- `subprocess`: 系统命令执行
- `datetime`: 日期时间处理
- `re`: 正则表达式
- `codecs`: 编码处理

## 🚀 GitHub Releases 自动发布

### 1. 准备工作

确保项目包含以下文件：

- `.github/workflows/release.yml`
- `upnp_gui.py`
- `requirements.txt`
- `README.md`
- `LICENSE`

### 2. 创建 Release

#### 方法 1：通过 Git 标签（推荐）

```bash
# 提交所有更改
git add .
git commit -m "feat: 准备发布 v1.0.0"

# 创建并推送标签
git tag v1.0.0
git push origin main
git push origin v1.0.0
```

#### 方法 2：通过 GitHub 界面

1. 访问 GitHub 仓库
2. 点击 "Releases" → "Create a new release"
3. 输入标签版本（如 v1.0.0）
4. 输入发布标题和描述
5. 点击 "Publish release"

### 3. 自动化流程

GitHub Actions 会自动：

1. 检测到新标签
2. 在 Windows 和 Linux 环境中构建
3. 创建 Release
4. 上传可执行文件

## 📋 发布检查清单

### 发布前检查

- [ ] 代码已测试
- [ ] README.md 已更新
- [ ] 版本号已更新
- [ ] 所有功能正常
- [ ] UTF-8 编码测试通过
- [ ] 构建脚本正常工作

### 发布后检查

- [ ] Release 文件可下载
- [ ] Windows 版本可运行
- [ ] Linux 版本可运行
- [ ] 功能完整性测试
- [ ] 文档链接正确

## 🐛 常见问题

### 构建失败

#### UTF-8 编码问题

```bash
# 测试编码支持
python test_utf8.py

# Windows系统设置
chcp 65001

# Linux系统设置
export LANG=C.UTF-8
```

#### 缺少依赖

```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

#### 权限问题

```bash
# Windows管理员权限
# 以管理员身份运行命令提示符

# Linux权限
chmod +x build.sh
```

### 运行失败

#### 缺少库文件

- 确保目标系统有必要的运行时库
- 检查防火墙设置
- 确保网络权限

#### 功能异常

- 检查路由器 UPnP 设置
- 确保网络连接正常
- 检查端口占用情况

## 📈 版本管理

### 版本号规则

使用语义化版本：`MAJOR.MINOR.PATCH`

- **MAJOR**: 重大功能变更
- **MINOR**: 新功能添加
- **PATCH**: 错误修复

### 发布流程

1. 开发新功能
2. 测试和修复
3. 更新版本号
4. 提交代码
5. 创建 Git 标签
6. 自动构建发布

## 🔮 未来计划

- [ ] macOS 支持
- [ ] 代码签名
- [ ] 自动更新
- [ ] 多语言支持
- [ ] 配置文件管理
- [ ] Docker 支持

## 📞 支持

如果遇到问题：

1. 查看本文档的常见问题部分
2. 运行 `python test_utf8.py` 测试环境
3. 提交 Issue 到 GitHub 仓库
4. 联系开发者

---

**注意**: 构建过程中请确保网络连接稳定，某些依赖可能需要从网络下载。
