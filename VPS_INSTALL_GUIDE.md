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

## 🔧 安装特性

### ✅ 精简安装
- **只下载核心文件**：media_packer_simple.py, start.py, requirements.txt
- **完整版可选**：使用 `--full` 参数才下载 media_packer_all_in_one.py
- **安装体积小**：避免下载不必要的文档和测试文件

### ✅ 智能依赖管理
脚本会按优先级尝试不同的依赖安装方式：

1. **用户模式安装**：`pip install --user` （首选）
2. **系统包绕过**：`pip install --user --break-system-packages` （现代Python限制）
3. **系统包管理器**：`apt install python3-torf` 等（Ubuntu/Debian）
4. **虚拟环境**：仅在其他方式失败时才使用

### ✅ 避免虚拟环境问题
- 虚拟环境仅作为最后选择
- 创建智能启动脚本自动处理环境激活
- 不会出现"Can not perform a '--user' install"错误

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
media-packer pack /path/to/video.mkv     # 直接制种
media-packer batch /path/to/videos/*     # 批量制种
media-packer interactive                 # 交互界面
```

### 方式2：直接运行Python脚本
```bash
cd ~/media-packer  # 进入安装目录
python3 media_packer_simple.py --help    # 查看帮助
python3 media_packer_simple.py pack /path/to/video.mkv
```

## 🔧 核心功能

- ✅ **智能CPU优化**：自动检测CPU核心数，优化线程配置
- ✅ **动态Piece Size**：根据文件大小自动选择最优Piece Size
- ✅ **系统负载监控**：实时监控CPU使用率，动态调整性能
- ✅ **精简部署**：只下载必要文件，避免冗余
- ✅ **智能依赖管理**：多种方式确保依赖安装成功

## 🖥️ VPS环境支持

### 支持的系统
- Ubuntu/Debian (18.04+)
- CentOS/RHEL (7+)
- Fedora (30+)
- macOS (10.14+)

### 依赖安装策略
1. 优先使用用户模式 pip 安装
2. 自动处理现代Python环境限制（Debian 12+, Ubuntu 23.04+）
3. 系统包管理器作为备选方案
4. 虚拟环境仅在必要时使用

## 📊 性能特性

当前系统会自动：
- 检测物理CPU核心数（使用psutil库）
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

### 常见问题解决

1. **externally-managed-environment 错误**
   ```bash
   # 脚本会自动处理，使用 --break-system-packages 参数
   ```

2. **虚拟环境中的 --user 错误**
   ```bash
   # 脚本已优化，避免在虚拟环境中使用 --user 参数
   ```

3. **手动重新安装**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --path /tmp/media-packer-new
   ```

4. **检查依赖**
   ```bash
   python3 -c "import torf, click, rich, psutil; print('所有依赖正常')"
   ```

## 🎉 优化亮点

- **精简下载**：只下载必要的3-4个文件，不是整个仓库
- **智能依赖**：4级依赖安装策略，确保99%安装成功
- **避免虚拟环境**：优先使用系统级安装方式
- **性能优先**：集成智能CPU检测和负载监控
- **一键使用**：安装完成即可直接使用制种功能

---

**享受极简高效的制种体验！** 🚀