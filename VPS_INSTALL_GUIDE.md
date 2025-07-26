# Media Packer - VPS一键安装指南

## 🚀 一键安装

### 基础安装（推荐）
```bash
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash
```

### 自定义安装选项
```bash
# 安装到指定目录
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --path /opt/media-packer

# 静默安装（无交互）
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --quiet

# 安装完整版（包含元数据功能）
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --full

# 跳过依赖安装（如果已安装）
curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --skip-deps
```

## 📝 安装参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--path PATH` | 安装目录 | `$HOME/media-packer` |
| `--simple` | 只安装简化版依赖 | ✓ 默认 |
| `--full` | 安装完整版依赖 | - |
| `--quiet` | 静默安装，无交互 | - |
| `--no-symlink` | 不创建系统命令链接 | - |
| `--skip-deps` | 跳过Python依赖安装 | - |

## 🎯 使用方法

安装完成后可以使用以下方式：

### 方式1：系统命令（推荐）
```bash
media-packer                              # 启动交互界面
media-packer pack /path/to/video.mkv     # 直接制种
media-packer batch /path/to/videos/*     # 批量制种
```

### 方式2：直接运行Python脚本
```bash
cd ~/media-packer  # 进入安装目录
python3 start.py                         # 启动交互界面
python3 media_packer_simple.py --help    # 查看帮助
```

## 🔧 核心功能

- ✅ **智能CPU优化**：自动检测CPU核心数，优化线程配置
- ✅ **动态Piece Size**：根据文件大小自动选择最优Piece Size
- ✅ **系统负载监控**：实时监控CPU使用率，动态调整性能
- ✅ **一键部署**：支持所有主流Linux发行版和macOS
- ✅ **虚拟环境支持**：自动处理现代Python环境限制

## 🖥️ VPS环境支持

### 支持的系统
- Ubuntu/Debian (18.04+)
- CentOS/RHEL (7+)
- Fedora (30+)
- macOS (10.14+)

### 自动环境适配
- 自动检测Python版本和包管理器
- 智能处理Python环境限制问题
- 自动创建虚拟环境（当需要时）
- 支持多种依赖安装方式

## 📊 性能特性

当前系统会自动：
- 检测物理CPU核心数
- 监控系统负载和CPU使用率
- 根据文件大小选择最优Piece Size配置
- 动态调整工作线程数以获得最佳性能

无需手动配置，一切都是自动优化！

## ⚡ 常见使用场景

### PT站制种
```bash
# 快速制种单个文件
media-packer pack /data/movie.mkv --name "MovieName.2024.1080p.BluRay.x264"

# 批量制种多个文件
media-packer batch /data/movies/* --organize
```

### VPS自动化
```bash
# 结合定时任务
echo "0 * * * * /usr/local/bin/media-packer batch /data/new/* --name 'Auto_$(date +\%Y\%m\%d_\%H)'" | crontab -
```

## 🛠️ 故障排除

如果遇到问题，可以：

1. **重新安装**：
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --path /tmp/media-packer-new
   ```

2. **检查依赖**：
   ```bash
   python3 -c "import torf, click, rich, psutil; print('所有依赖正常')"
   ```

3. **手动安装依赖**：
   ```bash
   python3 -m pip install --user torf click rich psutil
   ```

---

**享受高性能制种体验！** 🎉