# Media Packer - 智能影视制种工具

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

基于 torf 的智能影视剧打包制种工具，专为影视内容制作标准化 torrent 文件。具有友好的交互式界面和强大的命令行功能。

## ✨ 功能特性

- 🎯 **智能文件识别** - 自动识别视频格式、提取技术参数（分辨率、编码等）
- 📂 **标准化命名** - 支持电视剧和电影的标准化文件命名规范
- 🌐 **元数据集成** - 从 TMDB 获取完整的影视剧信息
- ⚡ **批量处理** - 支持批量文件处理和自动化工作流
- 🔧 **制种优化** - 基于 torf 的高效 torrent 创建
- 📄 **NFO 生成** - 兼容 Kodi/Plex 的 NFO 文件生成
- 🖥️ **双模式界面** - 友好的交互式界面 + 强大的命令行工具
- 🚀 **快速配置** - 内置配置向导，新手友好

## 🎥 演示

### 交互式界面
```
╭────── 欢迎使用 Media Packer ──────╮
│ Media Packer - 终端交互式制种工具 │
│ 基于 torf 的专业影视制种解决方案  │
│                                   │
│ 功能特性:                         │
│ • 智能媒体文件识别和处理          │
│ • 标准化文件命名和组织            │
│ • TMDB 元数据自动获取             │
│ • 批量处理和制种队列              │
│ • 交互式操作界面                  │
╰───────────────────────────────────╯
```

## 🚀 快速开始

### 依赖安装

```bash
pip install torf pymediainfo tmdbv3api requests click rich
```

### 基本使用

#### 交互式模式（推荐新用户）
```bash
# 直接运行，启动交互界面
python3 media_packer_all_in_one.py
```

首次使用会显示欢迎界面，选择"快速配置向导"完成基本设置：
1. 设置媒体目录（存放视频文件的文件夹）
2. 设置输出目录（种子文件保存位置）
3. 配置 Tracker（可使用内置示例）

#### 命令行模式（适合高级用户）
```bash
# 打包单个文件
python3 media_packer_all_in_one.py pack /path/to/video.mkv --organize --fetch-metadata

# 批量制种
python3 media_packer_all_in_one.py batch /path/to/season1 /path/to/season2 --name "TV Show Complete"

# 搜索元数据
python3 media_packer_all_in_one.py search "Breaking Bad" --type tv --year 2008
```

## 📖 详细文档

### 安装依赖详解

所需依赖说明：
- `torf` - 核心种子创建库
- `pymediainfo` - 媒体文件信息提取
- `tmdbv3api` - TMDB 元数据获取
- `requests` - HTTP 请求处理
- `click` - 命令行界面框架
- `rich` - 美化终端输出

### 配置说明

#### 环境变量（可选）
```bash
export TMDB_API_KEY="your_tmdb_api_key_here"  # TMDB API 密钥
export MP_OUTPUT_DIR="/path/to/output"        # 默认输出目录
```

#### 配置文件示例
```json
{
  "torrent": {
    "trackers": [
      "https://tracker1.example.com/announce",
      "https://tracker2.example.com/announce"
    ],
    "private": true,
    "comment": "Created with Media Packer"
  },
  "naming": {
    "tv_format": "{title} ({year}) S{season:02d}E{episode:02d} [{resolution}] [{codec}]",
    "movie_format": "{title} ({year}) [{resolution}] [{codec}]"
  },
  "tmdb_api_key": "your_tmdb_api_key_here",
  "output_dir": "./output"
}
```

### 文件组织规范

#### 电视剧结构
```
剧名 (年份) [分辨率] [编码]/
├── Season 01/
│   ├── 剧名 (年份) S01E01 [1080p] [H.264].mkv
│   ├── 剧名 (年份) S01E01 [1080p] [H.264].srt
│   └── 剧名 (年份) S01E01 [1080p] [H.264].nfo
├── Season 02/
└── tvshow.nfo
```

#### 电影结构
```
电影名 (年份) [分辨率] [编码]/
├── 电影名 (年份) [1080p] [H.264].mkv
├── 电影名 (年份) [1080p] [H.264].srt
└── 电影名 (年份) [1080p] [H.264].nfo
```

## 🛠️ 高级用法

### Python API
```python
from media_packer_all_in_one import MediaPacker, Config

# 创建配置
config = Config(
    trackers=["https://tracker.example.com/announce"],
    output_dir=Path("./output")
)

# 创建处理器
packer = MediaPacker(config)

# 处理文件
result = packer.process_file(
    Path("video.mkv"),
    organize=True,
    fetch_metadata=True,
    create_nfo=True
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
python3 media_packer_all_in_one.py pack [OPTIONS] INPUT_PATH

选项:
  -o, --output PATH       输出目录
  --organize             组织文件结构
  --fetch-metadata       获取元数据
  --create-nfo           创建 NFO 文件
```

#### batch - 批量制种
```bash
python3 media_packer_all_in_one.py batch [OPTIONS] INPUT_PATHS...

选项:
  -o, --output PATH       输出目录
  -n, --name TEXT         种子名称 [必需]
```

#### search - 搜索元数据
```bash
python3 media_packer_all_in_one.py search [OPTIONS] QUERY

选项:
  --type [tv|movie]       媒体类型 (默认: tv)
  --year INTEGER          发布年份
```

#### info - 种子信息
```bash
python3 media_packer_all_in_one.py info TORRENT_PATH
```

#### interactive - 交互模式
```bash
python3 media_packer_all_in_one.py interactive
```

## 🧪 测试

运行测试脚本验证功能：
```bash
python3 test_optimized.py
```

测试内容包括：
- 基本导入功能
- 文件检测功能
- 媒体类型识别
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
- [TMDB](https://www.themoviedb.org/) - 提供电影和电视剧元数据

## 📞 支持

如果遇到问题或有建议，请：
1. 查看 [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
2. 提交 [Issue](https://github.com/Yan-nian/media-packer/issues)
3. 发起 [Discussion](https://github.com/Yan-nian/media-packer/discussions)

---

**享受使用 Media Packer！** 🎉