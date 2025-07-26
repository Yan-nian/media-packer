# Media Packer VPS 部署完整指南

## 🎯 概述

本指南详细介绍如何在VPS服务器上部署和使用Media Packer，包括不同Linux发行版的安装方法、自动化脚本、故障排除等。

## 🖥️ 系统要求

### 最低配置
- **CPU**: 1核心
- **内存**: 512MB RAM
- **存储**: 1GB可用空间（不包括媒体文件）
- **系统**: Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- **Python**: 3.8或更高版本

### 推荐配置
- **CPU**: 2核心或更多
- **内存**: 1GB RAM或更多
- **存储**: 5GB可用空间
- **网络**: 稳定的互联网连接

## 🚀 一键部署脚本

### Ubuntu/Debian 一键部署
```bash
#!/bin/bash
# Ubuntu/Debian 一键部署脚本

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Media Packer VPS 一键部署 ===${NC}"

# 1. 更新系统
echo -e "${YELLOW}更新系统包...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. 安装必要软件
echo -e "${YELLOW}安装Python3和Git...${NC}"
sudo apt install python3 python3-pip git curl wget -y

# 3. 检查Python版本
PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
if [ "$PYTHON_VERSION" -lt 38 ]; then
    echo -e "${RED}Python版本过低，尝试安装Python3.9...${NC}"
    sudo apt install python3.9 python3.9-pip -y
    PYTHON_CMD="python3.9"
else
    PYTHON_CMD="python3"
fi

# 4. 下载项目
echo -e "${YELLOW}下载Media Packer...${NC}"
if [ -d "media-packer" ]; then
    echo -e "${YELLOW}目录已存在，更新代码...${NC}"
    cd media-packer
    git pull
else
    git clone https://github.com/Yan-nian/media-packer.git
    cd media-packer
fi

# 5. 设置权限
chmod +x setup.sh

# 6. 启动程序
echo -e "${GREEN}启动Media Packer...${NC}"
$PYTHON_CMD start.py

echo -e "${GREEN}部署完成！${NC}"
```

### CentOS/RHEL 一键部署
```bash
#!/bin/bash
# CentOS/RHEL 一键部署脚本

echo "=== Media Packer VPS 一键部署 (CentOS/RHEL) ==="

# 1. 更新系统
echo "更新系统包..."
sudo yum update -y

# 2. 安装EPEL仓库（如果需要）
sudo yum install epel-release -y

# 3. 安装必要软件
echo "安装Python3和Git..."
sudo yum install python3 python3-pip git curl wget -y

# 4. 下载项目
echo "下载Media Packer..."
if [ -d "media-packer" ]; then
    echo "目录已存在，更新代码..."
    cd media-packer
    git pull
else
    git clone https://github.com/Yan-nian/media-packer.git
    cd media-packer
fi

# 5. 启动程序
echo "启动Media Packer..."
python3 start.py

echo "部署完成！"
```

## 📋 分步安装指南

### 步骤1: 系统准备

#### Ubuntu/Debian
```bash
# 1. 连接到VPS
ssh user@your-vps-ip

# 2. 更新系统
sudo apt update && sudo apt upgrade -y

# 3. 安装基础软件
sudo apt install python3 python3-pip git curl wget htop nano -y
```

#### CentOS/RHEL
```bash
# 1. 连接到VPS
ssh user@your-vps-ip

# 2. 更新系统
sudo yum update -y

# 3. 安装基础软件
sudo yum install python3 python3-pip git curl wget htop nano -y
```

### 步骤2: 下载和安装

```bash
# 1. 下载项目
git clone https://github.com/Yan-nian/media-packer.git
cd media-packer

# 2. 检查Python版本
python3 --version

# 3. 一键启动（自动安装依赖）
python3 start.py
```

### 步骤3: 首次配置

```bash
# 程序会显示选择界面：
# 1. 简化版 (推荐) - 只生成种子文件，依赖最少
# 2. 完整版 - 包含元数据获取和NFO生成
# 3. 退出

# 选择1（简化版），然后程序会自动安装依赖
```

## 🔧 高级配置

### 创建服务脚本

#### 1. 创建Systemd服务
```bash
# 创建服务文件
sudo nano /etc/systemd/system/media-packer.service

# 添加以下内容：
[Unit]
Description=Media Packer Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/media-packer
ExecStart=/usr/bin/python3 media_packer_simple.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

# 启用和启动服务
sudo systemctl daemon-reload
sudo systemctl enable media-packer
sudo systemctl start media-packer
```

#### 2. 创建定时任务
```bash
# 编辑crontab
crontab -e

# 添加定时任务（每小时检查新文件）
0 * * * * cd /path/to/media-packer && python3 media_packer_simple.py batch /data/new_videos/* --name "Auto_$(date +\%Y\%m\%d_\%H)" > /var/log/media-packer.log 2>&1
```

### 环境变量配置

```bash
# 创建配置文件
nano ~/.media_packer_config

# 添加配置
export MEDIA_PACKER_OUTPUT_DIR="/data/torrents"
export MEDIA_PACKER_TEMP_DIR="/tmp/media_packer"
export MEDIA_PACKER_AUTO_INSTALL="yes"

# 加载配置
echo "source ~/.media_packer_config" >> ~/.bashrc
source ~/.bashrc
```

## 🎮 实际使用案例

### 案例1: PT站自动制种

```bash
#!/bin/bash
# PT站自动制种脚本

WATCH_DIR="/data/downloads"
OUTPUT_DIR="/data/torrents"
PROCESSED_DIR="/data/processed"

# 监控下载目录
inotifywait -m -r -e create,moved_to "$WATCH_DIR" --format '%w%f' |
while read file; do
    # 等待文件下载完成
    sleep 30
    
    if [[ "$file" =~ \.(mkv|mp4|avi|mov)$ ]]; then
        echo "处理文件: $file"
        
        # 获取文件夹名称作为种子名称
        folder_name=$(basename "$(dirname "$file")")
        
        # 创建种子
        cd /path/to/media-packer
        python3 media_packer_simple.py pack "$file" \
            --output "$OUTPUT_DIR" \
            --name "$folder_name" \
            --organize
        
        # 移动已处理文件
        mv "$file" "$PROCESSED_DIR/"
        
        echo "文件处理完成: $folder_name.torrent"
    fi
done
```

### 案例2: Web API 服务

```python
#!/usr/bin/env python3
# Media Packer Web API

from flask import Flask, request, jsonify, send_file
import os
import subprocess
import tempfile
from pathlib import Path

app = Flask(__name__)

MEDIA_PACKER_PATH = "/path/to/media-packer"
OUTPUT_DIR = "/data/torrents"

@app.route('/api/create_torrent', methods=['POST'])
def create_torrent():
    """创建种子API"""
    try:
        data = request.json
        file_path = data.get('file_path')
        torrent_name = data.get('name', 'auto_torrent')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 400
        
        # 执行制种命令
        cmd = [
            'python3', 'media_packer_simple.py', 'pack',
            file_path, '--name', torrent_name, '--output', OUTPUT_DIR
        ]
        
        result = subprocess.run(cmd, cwd=MEDIA_PACKER_PATH, 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            torrent_path = f"{OUTPUT_DIR}/{torrent_name}.torrent"
            return jsonify({
                'status': 'success',
                'torrent_name': f"{torrent_name}.torrent",
                'torrent_path': torrent_path
            })
        else:
            return jsonify({'error': result.stderr}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_torrent/<torrent_name>')
def download_torrent(torrent_name):
    """下载种子文件"""
    torrent_path = os.path.join(OUTPUT_DIR, torrent_name)
    if os.path.exists(torrent_path):
        return send_file(torrent_path, as_attachment=True)
    else:
        return jsonify({'error': '种子文件不存在'}), 404

@app.route('/api/status')
def status():
    """服务状态"""
    return jsonify({
        'status': 'running',
        'output_dir': OUTPUT_DIR,
        'torrent_count': len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.torrent')])
    })

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=8080, debug=False)
```

### 案例3: Docker 部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 克隆项目
RUN git clone https://github.com/Yan-nian/media-packer.git .

# 安装Python依赖
RUN python3 install_deps.py --mode simple

# 创建卷挂载点
VOLUME ["/data/input", "/data/output"]

# 暴露端口（如果使用API）
EXPOSE 8080

# 启动命令
CMD ["python3", "media_packer_simple.py"]
```

```bash
# 构建和运行Docker容器
docker build -t media-packer .

docker run -d \
    --name media-packer \
    -v /your/media/path:/data/input \
    -v /your/torrent/path:/data/output \
    -p 8080:8080 \
    media-packer
```

## 🛠️ 故障排除

### 常见问题

#### 1. 内存不足
```bash
# 症状：程序运行时内存占用过高或崩溃
# 解决方案：

# 检查内存使用
free -h
htop

# 创建交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用交换空间
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 2. 磁盘空间不足
```bash
# 检查磁盘使用
df -h
du -sh * | sort -hr

# 清理系统
sudo apt autoremove -y
sudo apt autoclean
docker system prune -f  # 如果使用Docker

# 移动输出目录到大容量磁盘
sudo mkdir -p /mnt/large_disk/torrents
sudo chown $USER:$USER /mnt/large_disk/torrents
python3 media_packer_simple.py pack video.mkv --output /mnt/large_disk/torrents
```

#### 3. 网络连接问题
```bash
# 使用国内镜像
python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple torf click rich

# 设置pip配置文件
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
EOF
```

#### 4. 权限问题
```bash
# 用户安装模式
python3 -m pip install --user torf click rich

# 设置PATH
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 修改文件权限
sudo chown -R $USER:$USER /path/to/media-packer
chmod +x setup.sh
```

### 日志和监控

#### 1. 启用详细日志
```bash
# 创建日志目录
mkdir -p ~/logs

# 运行时输出日志
python3 media_packer_simple.py pack video.mkv 2>&1 | tee ~/logs/media_packer.log

# 使用logrotate管理日志
sudo nano /etc/logrotate.d/media-packer
```

#### 2. 系统监控
```bash
# 安装监控工具
sudo apt install htop iotop nethogs -y

# 监控CPU和内存
htop

# 监控磁盘I/O
iotop

# 监控网络
nethogs
```

## 🔐 安全建议

### 1. 基础安全
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 配置防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8080  # 如果使用Web API

# 创建非root用户
sudo adduser media_packer
sudo usermod -aG sudo media_packer
```

### 2. SSH安全
```bash
# 修改SSH配置
sudo nano /etc/ssh/sshd_config

# 禁用root登录
PermitRootLogin no

# 修改默认端口
Port 2222

# 重启SSH服务
sudo systemctl restart sshd
```

### 3. 文件权限
```bash
# 设置合适的文件权限
chmod 755 ~/media-packer
chmod 644 ~/media-packer/*.py
chmod +x ~/media-packer/setup.sh

# 限制输出目录权限
chmod 700 /data/torrents
```

## 📊 性能优化

### 1. 系统优化
```bash
# 调整文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 调整内核参数
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
echo "net.core.rmem_max=16777216" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 2. Python优化
```bash
# 使用pypy（如果兼容）
sudo apt install pypy3 pypy3-pip -y
pypy3 media_packer_simple.py

# 设置Python优化
export PYTHONOPTIMIZE=1
export PYTHONHASHSEED=0
```

## 📈 扩展功能

### 1. 多实例部署
```bash
# 创建多个工作目录
for i in {1..4}; do
    cp -r media-packer media-packer-$i
    cd media-packer-$i
    # 使用不同端口启动
    python3 api_wrapper.py --port $((8080 + i)) &
    cd ..
done
```

### 2. 负载均衡
```nginx
# Nginx配置
upstream media_packer {
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
    server 127.0.0.1:8083;
    server 127.0.0.1:8084;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://media_packer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

**总结：通过本指南，你可以在任何VPS上快速部署Media Packer，无论是简单的单次使用还是复杂的自动化系统，都能找到合适的方案。** 🚀
