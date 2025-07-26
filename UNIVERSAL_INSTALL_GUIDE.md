# Universal Install Script 说明文档

## 概述

`universal-install.sh` 是 Media Packer 的通用智能安装脚本，能够自动检测系统环境并选择最佳的安装方式。无需Git克隆整个仓库，一条命令即可完成安装。

## 核心特性

### 🚀 智能检测
- **自动系统识别**: 支持 Ubuntu/Debian、CentOS/RHEL、Fedora、Arch Linux、macOS
- **Python版本检测**: 自动查找并使用最合适的Python版本（3.8+）
- **架构识别**: 支持 x86_64、ARM64 等主流架构
- **网络连接检查**: 验证GitHub连接是否正常

### 🔧 多种安装模式
- **快速安装**: 自动选择最佳安装方式
- **简化版安装**: 仅安装核心功能（torf, click, rich）
- **完整版安装**: 安装所有功能包括元数据支持
- **自定义安装**: 手动选择安装配置
- **环境检查**: 仅检查系统环境，不进行安装

### 📦 智能依赖管理
- **多种安装策略**: 用户安装、虚拟环境、系统包管理器
- **自动降级处理**: 处理 externally-managed-environment 限制
- **依赖冲突解决**: 自动处理不同Python环境的依赖问题

## 使用方法

### 基本使用

```bash
# 默认智能安装
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash
```

### 命令行参数

```bash
# 显示帮助
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --help

# 静默安装（使用默认选项）
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet

# 强制重新安装
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --force

# 仅安装简化版
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --simple

# 安装完整版
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --full

# 仅检查环境
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --check

# 指定安装路径
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --path /opt/media-packer
```

### 组合使用

```bash
# 静默安装简化版到指定目录
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet --simple --path ~/my-media-packer

# 强制重新安装完整版
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --force --full
```

## 安装流程

### 1. 环境检测阶段
- 检测操作系统类型和发行版
- 识别系统架构
- 检查网络连接
- 查找合适的Python版本

### 2. 安装配置阶段
- 根据模式选择要下载的文件
- 创建安装目录
- 下载必要的项目文件

### 3. 依赖安装阶段
- 尝试多种安装策略
- 处理现代Python环境限制
- 自动创建虚拟环境（如需要）

### 4. 环境配置阶段
- 创建启动脚本
- 配置PATH环境变量
- 创建桌面快捷方式（可选）

### 5. 测试验证阶段
- 验证依赖安装
- 测试程序启动
- 显示使用说明

## 支持的安装策略

### 用户安装模式
```bash
python3 -m pip install --user package_name
```
适用于大多数Linux发行版，安装到用户目录。

### 用户安装+Break System Packages
```bash
python3 -m pip install --user --break-system-packages package_name
```
适用于Ubuntu 23.04+、Debian 12+等现代系统。

### 虚拟环境模式
```bash
python3 -m venv ~/.media-packer/venv
source ~/.media-packer/venv/bin/activate
pip install package_name
```
最安全的安装方式，不影响系统Python环境。

### 系统包管理器
```bash
# Ubuntu/Debian
sudo apt install python3-package

# CentOS/RHEL
sudo yum install python3-package

# Fedora
sudo dnf install python3-package
```
使用系统包管理器安装Python包。

## 创建的文件结构

安装完成后会创建以下结构：

```
~/.media-packer/
├── media_packer_simple.py      # 简化版主程序
├── media_packer_all_in_one.py  # 完整版主程序（可选）
├── install_deps.py             # 依赖管理工具
├── requirements.txt            # 依赖列表
├── media-packer                # 主启动脚本
├── media-packer-full           # 完整版启动脚本
├── media-packer-deps           # 依赖管理脚本
└── venv/                       # 虚拟环境（如果使用）
    ├── bin/
    ├── lib/
    └── ...
```

## 启动脚本说明

### media-packer
主启动脚本，默认使用简化版程序。

```bash
media-packer                    # 交互式使用
media-packer pack video.mkv    # 生成种子
media-packer --help            # 显示帮助
```

### media-packer-full
完整版启动脚本，使用包含所有功能的版本。

```bash
media-packer-full               # 使用完整版
```

### media-packer-deps
依赖管理脚本，用于管理Python包。

```bash
media-packer-deps --mode simple  # 安装简化版依赖
media-packer-deps --mode full    # 安装完整版依赖
media-packer-deps --force        # 强制重新安装
```

## 故障排除

### 网络连接问题
```bash
# 使用代理
export https_proxy=http://proxy.example.com:8080
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash

# 使用镜像（如果有的话）
# 修改脚本中的GITHUB_RAW变量
```

### Python版本问题
```bash
# 检查可用的Python版本
ls /usr/bin/python*

# 手动指定Python版本
export PYTHON_CMD=python3.9
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash
```

### 权限问题
```bash
# 确保有写入权限
mkdir -p ~/.media-packer
chmod 755 ~/.media-packer

# 如果需要sudo权限安装系统包
sudo -v  # 先验证sudo权限
```

### 依赖安装失败
```bash
# 手动安装依赖
python3 -m pip install --user torf click rich

# 使用虚拟环境
python3 -m venv ~/.media-packer/venv
source ~/.media-packer/venv/bin/activate
pip install torf click rich
```

## 卸载方法

```bash
# 删除安装目录
rm -rf ~/.media-packer

# 清理环境变量（手动编辑配置文件）
vim ~/.bashrc  # 或 ~/.zshrc
# 删除包含 "media-packer" 的行

# 删除桌面快捷方式
rm -f ~/Desktop/media-packer.desktop
```

## 开发者信息

- **脚本版本**: 2.0.0
- **支持的Python版本**: 3.8+
- **支持的操作系统**: Linux、macOS、Windows(WSL)
- **脚本大小**: ~25KB
- **预计安装时间**: 1-3分钟（取决于网络速度）

## 与其他安装方式对比

| 特性 | universal-install.sh | install.sh | quick-use.sh |
|------|---------------------|------------|--------------|
| 智能检测 | ✅ | ❌ | ❌ |
| 自定义配置 | ✅ | ❌ | ❌ |
| 虚拟环境支持 | ✅ | ✅ | ❌ |
| 多种安装策略 | ✅ | ✅ | ✅ |
| 桌面快捷方式 | ✅ | ❌ | ❌ |
| 环境检查模式 | ✅ | ❌ | ❌ |
| 详细错误处理 | ✅ | ✅ | ✅ |
| 跨平台支持 | ✅ | ✅ | ✅ |

## 总结

`universal-install.sh` 是 Media Packer 最推荐的安装方式，它结合了智能检测、灵活配置和强大的错误处理能力，确保在各种环境下都能成功安装并正常运行。
