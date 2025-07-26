# 现代Python环境依赖安装指南

## 🔧 问题描述

如果你遇到以下错误：
```
error: externally-managed-environment
× This environment is externally managed
```

这是因为现代Linux发行版（Ubuntu 23.04+, Debian 12+）为了保护系统Python环境而限制了全局包安装。

## 🚀 解决方案

### 方案1: 使用我们的一键安装脚本（推荐）
```bash
# 我们的脚本已经处理了这个问题
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/install.sh | bash
```

### 方案2: 手动创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv ~/.media-packer-env

# 激活虚拟环境
source ~/.media-packer-env/bin/activate

# 安装依赖
pip install torf click rich

# 使用程序
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/media_packer_simple.py -o media_packer_simple.py
python media_packer_simple.py

# 退出虚拟环境
deactivate
```

### 方案3: 使用 --break-system-packages（谨慎使用）
```bash
python3 -m pip install --user --break-system-packages torf click rich
```

### 方案4: 使用pipx（如果可用）
```bash
# 安装pipx
sudo apt install pipx

# 使用pipx安装（每个包单独管理）
pipx install torf
pipx install click
pipx install rich
```

### 方案5: 系统包管理器
```bash
# Ubuntu/Debian
sudo apt install python3-pip python3-venv

# 然后重试用户安装
python3 -m pip install --user torf click rich
```

## 🎯 我们的解决方案

我们的安装脚本 (`install.sh` 和 `quick-use.sh`) 已经自动处理了这些问题：

1. **自动尝试多种安装方式**
2. **创建虚拟环境（如果需要）**
3. **使用正确的Python路径**
4. **提供详细的错误提示**

## 📋 使用建议

### 推荐做法
```bash
# 最简单的方式
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash

# 或者安装到本地
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/install.sh | bash
```

### 开发者做法
```bash
# 如果你要开发或修改代码
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python media_packer_simple.py
```

## 🔍 故障排除

### 检查Python环境
```bash
# 检查Python版本
python3 --version

# 检查pip版本
python3 -m pip --version

# 检查是否有venv模块
python3 -m venv --help
```

### 检查系统限制
```bash
# 查看是否有EXTERNALLY-MANAGED文件
ls -la /usr/lib/python*/EXTERNALLY-MANAGED

# 如果存在，说明系统启用了保护机制
```

### 强制安装（不推荐）
```bash
# 只有在确定不会破坏系统的情况下使用
python3 -m pip install --user --break-system-packages torf click rich
```

## 💡 为什么会有这个限制？

现代Linux发行版引入这个限制是为了：
1. **保护系统稳定性** - 防止用户安装的包影响系统包
2. **避免冲突** - 防止pip和系统包管理器冲突
3. **鼓励最佳实践** - 推荐使用虚拟环境

## ✅ 总结

我们的Media Packer已经自动处理了这些问题，你只需要：

1. **使用我们的一键脚本** - 自动处理所有兼容性问题
2. **如果失败，查看错误提示** - 我们提供了详细的解决方案
3. **需要时手动创建虚拟环境** - 按照上面的指南操作

**现在就试试我们的一键安装：**
```bash
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/install.sh | bash
```
