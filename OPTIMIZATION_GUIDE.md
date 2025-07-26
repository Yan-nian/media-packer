# Media Packer 优化版使用指南

## 主要优化内容

### 1. 默认启动交互界面
- **直接运行脚本** (`python3 media_packer_all_in_one.py`) 现在会自动启动友好的交互式界面
- **命令行模式** 仍然可用，在有参数时自动切换 (`python3 media_packer_all_in_one.py --help`)

### 2. 快速配置向导
- 新增选项9"快速配置向导"，帮助新用户快速完成基本设置
- 自动检测缺失配置，引导用户逐步完成设置
- 智能默认值，减少用户输入负担

### 3. 改进的错误处理
- 更好的异常捕获和恢复机制
- 依赖缺失时的友好提示
- 非致命错误不会导致程序崩溃

### 4. 用户体验优化
- 更清晰的欢迎界面和操作提示
- 智能默认选项（首次使用推荐快速向导）
- 退出时显示命令行模式使用提示

## 使用方法

### 交互式模式（推荐）
```bash
# 直接运行，启动交互界面
python3 media_packer_all_in_one.py
```

### 命令行模式
```bash
# 查看帮助
python3 media_packer_all_in_one.py --help

# 打包单个文件
python3 media_packer_all_in_one.py pack /path/to/video.mkv --organize --fetch-metadata

# 批量制种
python3 media_packer_all_in_one.py batch /path/to/season1 /path/to/season2 --name "TV Show Complete"

# 搜索元数据
python3 media_packer_all_in_one.py search "Breaking Bad" --type tv --year 2008

# 查看种子信息
python3 media_packer_all_in_one.py info /path/to/file.torrent
```

## 快速开始

1. **首次运行**：
   ```bash
   python3 media_packer_all_in_one.py
   ```

2. **选择快速配置向导**（选项9）：
   - 设置媒体目录（存放视频文件的文件夹）
   - 设置输出目录（种子文件保存位置）  
   - 配置Tracker（可使用内置示例）

3. **扫描和处理**：
   - 选择选项4扫描媒体文件
   - 选择选项6开始批量处理

## 依赖安装

如果遇到依赖缺失错误，请运行：

```bash
pip install torf pymediainfo tmdbv3api requests click rich
```

## 配置说明

### 媒体目录
- 添加包含视频文件的文件夹
- 支持递归扫描子目录
- 可以添加多个目录

### 输出目录  
- 种子文件的保存位置
- 程序会自动创建目录

### Tracker配置
- 制作种子必需的announce URL
- 可使用内置示例或添加自定义tracker
- 支持 http/https/udp 协议

### TMDB API（可选）
- 用于获取影视剧元数据
- 设置环境变量：`export TMDB_API_KEY="your_api_key"`
- 或在配置文件中设置

## 测试验证

运行测试脚本验证功能：
```bash
python3 test_optimized.py
```

## 功能特性

- ✅ 智能媒体文件识别（视频格式、分辨率、编码）
- ✅ 标准化文件命名和组织结构
- ✅ TMDB元数据自动获取
- ✅ 批量处理和制种队列
- ✅ 交互式和命令行双模式
- ✅ 配置向导和设置保存
- ✅ 强大的错误处理和恢复

享受使用Media Packer优化版！🎉
