# Media Packer - 简化版种子生成工具

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

基于 torf 的简化版种子生成工具，专注于核心功能：为影视文件创建标准化 torrent 文件。

## ✨ 功能特性

- 🎯 **智能文件识别** - 自动识别视频格式和文件类型
- 📂 **智能命名** - 基于文件夹名称的种子命名
- ⚡ **批量处理** - 支持批量文件处理和自动化工作流
- 🔧 **制种优化** - 基于 torf 的高效 torrent 创建
- 🖥️ **双模式界面** - 友好的交互式界面 + 强大的命令行工具
- 🚀 **快速配置** - 内置配置向导，新手友好
- 🎛️ **专注核心** - 移除复杂功能，专注于种子生成

## 🎥 演示

### 交互式界面
```
╭────── 欢迎使用 Media Packer ──────╮
│ Media Packer - 简化版种子生成工具 │
│ 基于 torf 的专业种子生成解决方案  │
│                                   │
│ 功能特性:                         │
│ • 智能媒体文件识别和处理          │
│ • 基于文件夹名称的种子命名        │
│ • 批量处理和制种队列              │
│ • 交互式操作界面                  │
│ • 专注核心功能，简单易用          │
╰───────────────────────────────────╯
```

## 🚀 快速开始

### 🎯 一键启动（最简单）

我们提供了多种启动方式，选择最适合你的：

#### 方式1: 智能启动器
```bash
# 自动选择版本并安装依赖
python3 start.py
```

#### 方式2: Shell脚本（推荐Linux/macOS用户）
```bash
# 一键安装和启动
./setup.sh
```

#### 方式3: 直接运行（自动安装依赖）
```bash
# 简化版 - 自动检查和安装依赖
python3 media_packer_simple.py

# 完整版 - 自动检查和安装依赖
python3 media_packer_all_in_one.py
```

### 🔧 依赖管理

#### 自动依赖安装
程序首次运行时会自动：
- ✅ 检查所需依赖包
- ✅ 提示安装缺失的包  
- ✅ 一键下载和安装
- ✅ 自动重启程序

#### 手动依赖管理
```bash
# 使用专用的依赖安装工具
python3 install_deps.py --mode simple    # 安装简化版依赖
python3 install_deps.py --mode full      # 安装完整版依赖
python3 install_deps.py --force          # 强制重新安装

# 传统手动安装
pip install torf click rich              # 简化版
pip install torf pymediainfo tmdbv3api requests click rich  # 完整版
```

### 基本使用

#### 新用户（一键启动）
```bash
# 首次使用 - 自动安装依赖
python3 media_packer_simple.py
```

程序会自动：
- 检查所需依赖包
- 提示安装缺失的包
- 一键安装并重启程序

#### 高级用户
```bash
# 手动安装依赖后使用
pip install torf click rich
python3 media_packer_simple.py
```

首次使用会显示欢迎界面，选择"快速配置向导"完成基本设置：
1. 设置媒体目录（存放视频文件的文件夹）
2. 设置输出目录（种子文件保存位置）
3. 配置 Tracker

#### 命令行模式（适合高级用户）
```bash
# 打包单个文件（简化版）
python3 media_packer_simple.py pack /path/to/video.mkv --organize

# 批量制种（简化版）
python3 media_packer_simple.py batch /path/to/season1 /path/to/season2 --name "TV Show Complete"

# 查看种子信息
python3 media_packer_simple.py info /path/to/file.torrent
```

## 📖 详细文档

### 安装依赖详解

#### 简化版依赖
- `torf` - 核心种子创建库
- `click` - 命令行界面框架
- `rich` - 美化终端输出

#### 完整版依赖（如需元数据功能）
- `pymediainfo` - 媒体文件信息提取
- `tmdbv3api` - TMDB 元数据获取
- `requests` - HTTP 请求处理

### 配置说明

#### 基本配置
```python
config = Config(
    trackers=["https://tracker.example.com/announce"],
    output_dir=Path("./output"),
    private=True,
    comment="Created with Media Packer Simple"
)
```

### 文件组织规范

#### 简化版结构
```
输出目录/
├── 电影名称/
│   ├── movie.mkv
│   └── 电影名称.torrent
├── 剧集名称/
│   ├── episode1.mkv
│   ├── episode2.mkv
│   └── 剧集名称.torrent
```

## 🛠️ 高级用法

### Python API（简化版）
```python
from media_packer_simple import MediaPacker, Config

# 创建配置
config = Config(
    trackers=["https://tracker.example.com/announce"],
    output_dir=Path("./output")
)

# 创建处理器
packer = MediaPacker(config)

# 处理文件
torrent_path = packer.create_torrent_for_file(
    Path("video.mkv"),
    custom_name="Movie Name",
    organize=True
)
```

### 批量自动化
```python
# 批量处理多个文件
file_paths = [Path("season1/ep1.mkv"), Path("season1/ep2.mkv")]
torrent_path = packer.batch_process(file_paths, "Season 1 Complete")
```

## 📋 命令行参考

### 全局选项
- `-c, --config PATH` - 指定配置文件路径

### 命令列表

#### pack - 打包文件
```bash
python3 media_packer_simple.py pack [OPTIONS] INPUT_PATH

选项:
  -o, --output PATH       输出目录
  --organize             组织文件结构
  -n, --name TEXT        种子名称（默认使用文件夹名称）
```

#### batch - 批量制种
```bash
python3 media_packer_simple.py batch [OPTIONS] INPUT_PATHS...

选项:
  -o, --output PATH       输出目录
  -n, --name TEXT         种子名称 [必需]
```

#### info - 种子信息
```bash
python3 media_packer_simple.py info TORRENT_PATH
```

#### interactive - 交互模式
```bash
python3 media_packer_simple.py interactive
```

## 🧪 测试

运行测试脚本验证功能：
```bash
python3 test_simple.py
```

测试内容包括：
- 基本导入功能
- 文件检测功能
- 种子创建功能
- 命令行界面

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer

# 安装依赖
pip install -r requirements.txt

# 运行测试
python3 test_optimized.py
```

## 📄 许可证

本项目采用 [GPL-3.0](LICENSE) 许可证。

## 🙏 致谢

- [torf](https://github.com/rndusr/torf) - 优秀的 torrent 创建库
- [rich](https://github.com/Textualize/rich) - 美化终端输出
- [click](https://github.com/pallets/click) - 强大的命令行框架

## 📞 支持

如果遇到问题或有建议，请：
1. 查看 [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
2. 提交 [Issue](https://github.com/Yan-nian/media-packer/issues)
3. 发起 [Discussion](https://github.com/Yan-nian/media-packer/discussions)

---

**享受使用 Media Packer！** 🎉