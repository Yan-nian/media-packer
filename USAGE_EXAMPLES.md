# Media Packer 使用示例

## 🚀 一键使用示例

### 最简单的方式 - 立即使用
```bash
# 交互式使用
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash
```

### 命令行直接使用
```bash
# 生成单个种子
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack /path/to/video.mkv --name "My_Movie"

# 批量处理
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- batch /path/to/videos/* --name "Batch_Upload"

# 指定输出目录
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack ./movie.mkv --output ./torrents --name "MyTorrent"
```

### 安装到本地
```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/install.sh | bash

# 安装后使用（重新打开终端）
media-packer
media-packer pack /path/to/video.mkv --name "Local_Torrent"
```

## 🖥️ VPS 使用示例

### VPS 临时使用
```bash
# 连接到VPS
ssh user@your-vps-ip

# 直接使用，无需安装任何东西
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack /data/video.mkv --name "VPS_Torrent"
```

### VPS 安装使用
```bash
# 在VPS上安装
ssh user@your-vps-ip
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/install.sh | bash

# 以后直接使用
media-packer pack /data/video.mkv --name "VPS_Movie"
```

### VPS 自动化脚本
```bash
# 创建自动化脚本
cat > auto_torrent.sh << 'EOF'
#!/bin/bash
# 自动处理新视频文件
WATCH_DIR="/data/downloads"
OUTPUT_DIR="/data/torrents"

for file in "$WATCH_DIR"/*.{mkv,mp4,avi}; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" | sed 's/\.[^.]*$//')
        curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack "$file" --name "$filename" --output "$OUTPUT_DIR"
        echo "已处理: $filename"
    fi
done
EOF

chmod +x auto_torrent.sh
./auto_torrent.sh
```

## 📊 实际使用场景

### 场景1: 新用户第一次使用
```bash
# 什么都不用安装，直接试用
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash

# 程序会引导你：
# 1. 选择视频文件
# 2. 设置种子名称
# 3. 选择输出目录
# 4. 生成种子
```

### 场景2: PT站用户批量制种
```bash
# 方式1: 一次性批量处理
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- batch /path/to/download/* --organize

# 方式2: 安装后批量处理
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/install.sh | bash
media-packer batch /path/to/download/* --organize
```

### 场景3: VPS服务器自动化
```bash
# 设置定时任务
crontab -e

# 每30分钟检查新文件
*/30 * * * * /bin/bash -c 'curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- batch /data/new/* --name "Auto_$(date +\%H\%M)" --organize' > /var/log/auto-torrent.log 2>&1
```

### 场景4: 脚本集成
```bash
#!/bin/bash
# 下载完成后自动制种的脚本

DOWNLOAD_FILE="$1"
TORRENT_NAME="$2"

# 检查文件是否存在
if [ ! -f "$DOWNLOAD_FILE" ]; then
    echo "文件不存在: $DOWNLOAD_FILE"
    exit 1
fi

# 自动生成种子
echo "正在为 $DOWNLOAD_FILE 生成种子..."
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack "$DOWNLOAD_FILE" --name "$TORRENT_NAME" --output ./torrents

echo "种子生成完成: ${TORRENT_NAME}.torrent"
```

## 🔧 高级用法

### 参数说明
```bash
# 基本语法
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- [命令] [文件] [选项]

# 主要命令
pack        # 生成单个种子
batch       # 批量生成种子
info        # 查看种子信息
interactive # 交互模式（默认）

# 主要选项
--name TEXT      # 种子名称
--output PATH    # 输出目录
--organize       # 自动组织文件
--private        # 私有种子
--announce URL   # Tracker地址
```

### 环境变量
```bash
# 设置默认输出目录
export MEDIA_PACKER_OUTPUT="/data/torrents"

# 设置默认Tracker
export MEDIA_PACKER_ANNOUNCE="http://tracker.example.com/announce"

# 使用环境变量
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack video.mkv
```

## 🎯 最佳实践

### 1. 文件命名规范
```bash
# 使用有意义的名称
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack movie.mkv --name "Movie.Name.2023.1080p.BluRay.x264"

# 批量使用文件夹名
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- batch /downloads/*/
```

### 2. 输出组织
```bash
# 自动组织输出文件
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- batch /videos/* --organize --output /torrents
```

### 3. 日志记录
```bash
# 记录操作日志
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack video.mkv --name "MyMovie" 2>&1 | tee torrent-creation.log
```

---

**这些示例涵盖了从新手到高级用户的各种使用场景，选择适合你的方式开始使用吧！** 🎉
