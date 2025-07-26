#!/bin/bash
#
# Media Packer - 本地一键部署脚本
# 用于模拟和测试VPS部署流程
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
SOURCE_DIR="$(pwd)"
INSTALL_DIR="$HOME/media-packer-test"
MODE="simple"

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示横幅
echo -e "${CYAN}"
echo "╭─────────────────────────────────────────────────╮"
echo "│         Media Packer 本地部署测试器             │"
echo "│              模拟VPS安装流程                     │"
echo "╰─────────────────────────────────────────────────╯"
echo -e "${NC}"

# 创建测试安装目录
print_info "创建测试安装目录: $INSTALL_DIR"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 复制文件
print_info "复制核心文件..."
FILES=(
    "media_packer_simple.py"
    "media_packer_all_in_one.py" 
    "start.py"
    "install_deps.py"
    "requirements.txt"
    "pyproject.toml"
    "README.md"
    "CLAUDE.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$SOURCE_DIR/$file" ]; then
        cp "$SOURCE_DIR/$file" "$INSTALL_DIR/"
        print_info "复制 $file"
    else
        print_error "文件不存在: $file"
    fi
done

# 创建输出目录
mkdir -p "$INSTALL_DIR/output"

# 设置执行权限
chmod +x "$INSTALL_DIR"/*.py

# 检测Python和依赖
cd "$INSTALL_DIR"
print_info "检测Python环境..."

if python3 -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>/dev/null; then
    print_success "Python环境正常"
else
    print_error "Python环境异常"
    exit 1
fi

# 安装依赖
print_info "安装简化版依赖..."
if python3 -m pip install --user torf click rich psutil 2>/dev/null; then
    print_success "依赖安装成功"
else
    print_info "尝试使用系统包管理器安装..."
    python3 -m pip install --user --break-system-packages torf click rich psutil 2>/dev/null || {
        print_error "依赖安装失败"
        exit 1
    }
fi

# 创建启动脚本
print_info "创建启动命令..."
cat > media-packer << 'EOF'
#!/bin/bash
INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
cd "$INSTALL_DIR"
python3 start.py "$@"
EOF

chmod +x media-packer

# 创建配置文件
print_info "创建默认配置..."
cat > config.json << 'EOF'
{
    "auto_optimize": true,
    "output_dir": "./output",
    "private": true,
    "comment": "Created by Media Packer",
    "created_by": "Media Packer v2.0"
}
EOF

# 功能测试
print_info "运行功能测试..."
if python3 media_packer_simple.py --help >/dev/null 2>&1; then
    print_success "功能测试通过"
else
    print_error "功能测试失败"
    exit 1
fi

# 显示完成信息
print_success "本地部署测试完成！"
echo ""
echo -e "${CYAN}测试安装位置:${NC} $INSTALL_DIR"
echo ""
echo -e "${GREEN}测试命令:${NC}"
echo "  cd $INSTALL_DIR"
echo "  ./media-packer --help"
echo "  python3 media_packer_simple.py --help"
echo ""
echo -e "${YELLOW}VPS使用示例:${NC}"
echo "  curl -fsSL https://your-repo/quick-install.sh | bash"
echo "  curl -fsSL https://your-repo/quick-install.sh | bash -s -- --path /opt/media-packer"
echo "  curl -fsSL https://your-repo/quick-install.sh | bash -s -- --full --quiet"