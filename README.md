# Media Packer - 简化版种子生成工具

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

一个专门为PT站用户设计的轻量级种子制作工具，特别优化了文件夹命名和自动化流程。

## 🌟 一键使用

```bash
# ⚡ 通用一键安装（强烈推荐）- 自动检测系统，智能安装
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash

# 🤫 静默安装简化版
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet --simple

# 📦 安装完整版
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --full

# 🎯 自定义安装路径
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --path /opt/media-packer
```

**无需下载仓库，无需Git，一个命令搞定！**

## ✨ 主要特色

- 🎯 **简化操作** - 一键生成种子文件，无需复杂配置
- 🗂️ **智能命名** - 自动使用文件夹名称作为种子名称
- 🔄 **自动依赖安装** - 首次运行自动检查和安装所需包
- 🖥️ **多平台支持** - Windows、macOS、Linux全平台兼容
- 🚀 **VPS优化** - 专门为服务器环境优化的部署方案
- 📦 **零配置启动** - 下载即用，无需手动安装依赖
- 📊 **版本管理** - 完善的版本控制系统

## 🚀 快速开始

### ⚡ 一键使用（无需下载仓库）

#### 方式1: 通用智能安装（强烈推荐）
```bash
# 自动检测系统，智能选择最佳安装方式
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash

# 安装后直接使用
media-packer                              # 交互式使用
media-packer pack /path/to/video.mkv     # 直接生成种子
media-packer batch /path/to/videos/*     # 批量处理
```

#### 方式2: 静默安装（无交互）
```bash
# 静默安装简化版
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet --simple

# 静默安装完整版
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet --full
```

#### 方式3: 自定义安装
```bash
# 安装到指定目录
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --path /opt/media-packer

# 仅检查环境不安装
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --check
```

**特性：**
- ✅ **零配置** - 无需git，无需clone仓库
- ✅ **智能安装** - 自动检测系统，选择最佳安装方式
- ✅ **自动安装依赖** - 自动检查和安装Python包
- ✅ **跨平台** - 支持Linux、macOS、Windows(WSL)
- ✅ **多种模式** - 支持简化版、完整版、自定义安装

### 本地开发使用

#### 方式1: 传统Git方式（开发者）
```bash
# 下载项目
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer

# 智能启动器
python3 start.py

# 或直接运行
python3 media_packer_simple.py
```

#### 方式2: 直接下载使用
```bash
# 下载主程序文件
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/media_packer_simple.py -o media_packer_simple.py

# 安装依赖后直接使用
pip install torf click rich
python3 media_packer_simple.py
```

### 🖥️ VPS 服务器部署

#### ⚡ 一键智能安装（推荐）
```bash
# 通用智能安装（自动适配VPS环境）
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash

# VPS专用静默安装
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet --simple

# 安装后直接使用
media-packer pack /data/video.mkv --name "VPS_Torrent"
media-packer batch /data/videos/* --organize
```

#### 🎯 高级VPS使用
```bash
# 自定义VPS安装路径
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --path /opt/media-packer --quiet

# 批量处理多个文件
media-packer batch /data/videos/* --name "Batch_$(date +%Y%m%d)"

# 使用完整版（包含元数据功能）
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --full --quiet
media-packer-full pack /data/video.mkv
```

#### 🔧 VPS专用部署脚本（传统方式）
```bash
# 传统Git方式部署
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer
python3 start.py
```

**安装方式对比：**

| 安装方式 | 适用场景 | 特点 | 推荐指数 |
|---------|---------|------|----------|
| `universal-install.sh` | 所有用户 | 智能检测，最佳安装方式 | ⭐⭐⭐⭐⭐ |
| `universal-install.sh --simple` | 轻量使用 | 仅核心功能，快速安装 | ⭐⭐⭐⭐⭐ |
| `universal-install.sh --full` | 高级用户 | 完整功能，包含元数据 | ⭐⭐⭐⭐ |
| 直接下载 | 开发测试 | 手动管理，灵活控制 | ⭐⭐⭐ |

#### 📋 手动部署流程

**Ubuntu/Debian 系统：**
```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装必要软件
sudo apt install python3 python3-pip git curl wget -y

# 3. 下载项目
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer

# 4. 启动程序（自动安装Python依赖）
python3 start.py
```

**CentOS/RHEL 系统：**
```bash
# 1. 更新系统
sudo yum update -y

# 2. 安装EPEL和必要软件
sudo yum install epel-release -y
sudo yum install python3 python3-pip git curl wget -y

# 3. 下载项目
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer

# 4. 启动程序（自动安装Python依赖）
python3 start.py
```

#### 🔧 VPS 高级功能

**1. 脚本参数选项：**
```bash
# 查看帮助
./vps_quick_start.sh --help

# 仅更新项目代码
./vps_quick_start.sh --update

# 仅安装依赖
./vps_quick_start.sh --deps

# 静默模式（跳过确认）
./vps_quick_start.sh --silent
```

**2. 非交互式使用：**
```bash
# 直接生成种子（适合脚本和自动化）
python3 media_packer_simple.py pack /path/to/video.mkv --name "VPS_Torrent" --output /data/torrents
```

**3. 批量处理：**
```bash
# 批量处理多个文件
python3 media_packer_simple.py batch /data/videos/* --name "Batch_$(date +%Y%m%d)"
```

**💡 详细VPS部署指南**
完整的VPS部署文档请查看：[VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md)

包含内容：
- 📋 分步安装指南
- 🔧 高级配置（服务脚本、定时任务）
- 🎮 实际使用案例（PT站自动制种、Web API）
- 🛠️ 故障排除和性能优化
- 🔐 安全建议
- 📊 监控和日志管理

## ⚡ 依赖管理

### 自动依赖安装
程序首次运行时会自动：
- ✅ 检查所需依赖包
- ✅ 提示安装缺失的包  
- ✅ 一键下载和安装
- ✅ 自动重启程序

### 手动依赖管理
```bash
# 使用专用的依赖安装工具
python3 install_deps.py --mode simple    # 安装简化版依赖
python3 install_deps.py --mode full      # 安装完整版依赖
python3 install_deps.py --force          # 强制重新安装

# 传统手动安装
pip install torf click rich              # 简化版
pip install torf pymediainfo tmdbv3api requests click rich  # 完整版
```

## 🎯 基本使用

### 交互式界面
```bash
# 启动交互界面
python3 media_packer_simple.py

# 程序会引导你：
# 1. 选择媒体文件或文件夹
# 2. 设置种子名称（默认使用文件夹名）
# 3. 选择输出目录
# 4. 自动生成种子文件
```

### 命令行模式
```bash
# 基本用法
python3 media_packer_simple.py pack VIDEO_PATH

# 指定种子名称
python3 media_packer_simple.py pack VIDEO_PATH --name "My_Torrent"

# 指定输出目录
python3 media_packer_simple.py pack VIDEO_PATH --output ./torrents

# 批量处理
python3 media_packer_simple.py batch /path/to/videos/* --name "Batch_Upload"
```

## 📂 项目结构

```
media-packer/
├── 📄 README.md                    # 项目说明文档
├── 📄 VPS_DEPLOYMENT_GUIDE.md      # VPS部署完整指南
├── 📄 PYTHON_ENV_GUIDE.md          # Python环境问题解决指南
├── 📄 USAGE_EXAMPLES.md            # 详细使用示例
├── 🐍 start.py                     # 智能启动器
├── 🐍 media_packer_simple.py       # 简化版主程序
├── 🐍 media_packer_all_in_one.py   # 完整版主程序
├── 🐍 install_deps.py              # 依赖安装工具
├── 🔧 universal-install.sh         # 通用智能安装脚本（推荐）
├── 📋 requirements.txt             # Python依赖列表
├── 📦 pyproject.toml               # 项目配置
└── 📁 output/                      # 输出目录
```

## 🔄 版本差异

### 简化版 (media_packer_simple.py)
- **依赖最少** - 仅需 3 个包：`torf`, `click`, `rich`
- **功能精简** - 专注于种子生成核心功能
- **启动快速** - 依赖安装和程序启动都更快
- **资源占用少** - 适合VPS等资源受限环境
- **推荐用户** - 新用户、VPS用户、仅需种子生成功能的用户

### 完整版 (media_packer_all_in_one.py)
- **功能完整** - 包含元数据获取、NFO生成等高级功能
- **依赖较多** - 需要 6 个包，包含媒体分析库
- **功能丰富** - 支持TMDB元数据、媒体信息分析
- **推荐用户** - 高级用户、需要完整功能的用户

## 📡 VPS 常见使用场景

### 1. PT站自动制种
```bash
# 一键智能安装后使用
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash
media-packer batch /data/videos/* --organize

# 传统Git方式
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer
python3 media_packer_simple.py batch /data/videos/* --organize
```

### 2. 定时自动化
```bash
# 创建定时任务（使用安装版本）
crontab -e

# 每小时检查新文件并制种
0 * * * * /bin/bash -c 'media-packer batch /data/new_videos/* --name "Auto_$(date +%Y%m%d_%H)" > /var/log/media-packer.log 2>&1'
```

### 3. 一次性使用
```bash
# 智能安装后直接使用
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet
media-packer pack /data/video.mkv --name "MyTorrent" --output /data/torrents
```

### 3. API服务模式
```bash
# 启动Web API服务（需要额外安装Flask）
pip install flask
python3 api_wrapper.py --port 8080

# 通过API创建种子
curl -X POST http://vps-ip:8080/api/create_torrent \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/data/video.mkv", "name": "MyTorrent"}'
```

## 🛠️ VPS 故障排除

### 常见问题

#### 1. 现代Python环境限制问题
```bash
# 错误: externally-managed-environment
# 这是Ubuntu 23.04+/Debian 12+的新限制

# 解决方案1: 使用通用安装脚本（自动处理）
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash

# 解决方案2: 手动创建虚拟环境
python3 -m venv ~/.media-packer-env
source ~/.media-packer-env/bin/activate
pip install torf click rich

# 解决方案3: 使用break-system-packages（谨慎）
python3 -m pip install --user --break-system-packages torf click rich
```

#### 2. Python版本问题
```bash
# 检查Python版本
python3 --version

# 如果版本低于3.8，安装新版本
sudo apt install python3.9 python3.9-pip -y
python3.9 media_packer_simple.py
```

#### 3. 内存不足
```bash
# 检查内存使用
free -h

# 创建交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. 网络连接问题
```bash
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple torf click rich
```

#### 5. 磁盘空间不足
```bash
# 检查磁盘使用
df -h

# 清理系统
sudo apt autoremove -y
sudo apt autoclean
```

### 性能优化

#### 1. 系统优化
```bash
# 调整文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
```

#### 2. 使用SSD存储
```bash
# 将输出目录设置到SSD
python3 media_packer_simple.py pack video.mkv --output /ssd/torrents
```

## 🎨 高级功能

### 批量操作
```bash
# 批量处理多个文件
python3 media_packer_simple.py batch /data/videos/*.mkv --name "MyBatch"

# 自动组织输出文件
python3 media_packer_simple.py batch /data/videos/* --organize
```

### 种子信息查看和验证
```bash
# 查看种子详细信息
python3 media_packer_simple.py info TORRENT_PATH

# 验证种子文件
python3 media_packer_simple.py verify TORRENT_PATH
```

### 系统信息查看
```bash
# 查看系统信息和推荐配置
python3 media_packer_simple.py system_info
```

### 配置管理
```bash
# 设置默认配置
python3 media_packer_simple.py config --set-default-output /data/torrents
python3 media_packer_simple.py config --set-default-announce "http://tracker.example.com/announce"
```

## 📖 命令行参考

### 主要命令

#### pack - 生成单个种子
```bash
python3 media_packer_simple.py pack FILE_OR_FOLDER [OPTIONS]

选项:
  --name TEXT     种子名称（默认使用文件夹名）
  --output PATH   输出目录（默认: ./output）
  --announce URL  Tracker地址
  --comment TEXT  种子注释
  --private       创建私有种子
```

#### batch - 批量生成种子
```bash
python3 media_packer_simple.py batch FILES... [OPTIONS]

选项:
  --name TEXT     批次名称前缀
  --output PATH   输出目录
  --organize      自动组织输出文件
```

#### info - 查看种子信息
```bash
python3 media_packer_simple.py info TORRENT_PATH
```

#### verify - 验证种子文件
```bash
python3 media_packer_simple.py verify TORRENT_PATH
```

#### system_info - 显示系统信息
```bash
python3 media_packer_simple.py system_info
```

#### interactive - 交互模式
```bash
python3 media_packer_simple.py interactive
```

## 🔄 版本管理

Media Packer 使用语义化版本控制。当前版本为 v2.1.0。

### 查看版本
```bash
# 查看程序版本
python3 media_packer_simple.py --version

# 查看依赖安装工具版本
python3 install_deps.py --version

# 查看启动器版本
python3 start.py --version
```

### 更新日志
详细更新日志请查看 [CHANGELOG.md](CHANGELOG.md)

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献
1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 贡献类型
- 🐛 Bug报告和修复
- ✨ 新功能建议和实现
- 📚 文档改进
- 🎨 UI/UX改进
- 🔧 性能优化
- 🌐 国际化支持

## 📜 更新日志

### v2.1.0 (当前版本)
- ✨ 新增版本管理系统
- ✨ 新增种子文件验证功能
- ✨ 新增系统信息显示功能
- ✨ 新增进度条显示功能
- 🔧 优化制种脚本的性能配置推荐
- 🔧 增强内存限制检查
- 🔧 完善一键安装脚本，增强错误处理

### v2.0.0
- ✨ 新增VPS一键部署脚本
- ✨ 自动依赖检查和安装
- ✨ 智能启动器
- ✨ 完整的VPS部署指南
- 🔧 优化文件夹命名逻辑
- 🔧 改进错误处理
- 📚 完善文档和使用指南

### v1.0.0
- 🎉 初始版本发布
- ✅ 基本种子生成功能
- ✅ 交互式界面
- ✅ 跨平台支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [torf](https://github.com/rndusr/torf) - 优秀的种子文件处理库
- [click](https://github.com/pallets/click) - 强大的命令行界面库
- [rich](https://github.com/textualize/rich) - 美丽的终端输出库

## 📞 支持和反馈

如果遇到问题或有建议，请：
1. 查看 [UNIVERSAL_INSTALL_GUIDE.md](UNIVERSAL_INSTALL_GUIDE.md) - 通用安装脚本详细说明
2. 查看 [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md) - VPS部署完整指南
3. 查看 [PYTHON_ENV_GUIDE.md](PYTHON_ENV_GUIDE.md) - Python环境问题解决
4. 提交 [Issue](https://github.com/Yan-nian/media-packer/issues)
5. 发起 [Discussion](https://github.com/Yan-nian/media-packer/discussions)

---

**享受使用 Media Packer！** 🎉