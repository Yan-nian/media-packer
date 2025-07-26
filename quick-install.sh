#!/bin/bash
#
# Media Packer - 一键安装脚本
# 适用于 VPS 和本地环境快速部署
#
# 使用方法:
#   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --path /opt/media-packer
#   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --simple
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 默认配置
INSTALL_DIR="$HOME/media-packer"
MODE="simple"
QUIET=false
CREATE_SYMLINK=true
SKIP_DEPS=false
UPDATE_MODE=false
BACKUP_OLD=true
FORCE_INSTALL=false

# 版本信息
SCRIPT_VERSION="2.1.0"
VERSION_FILE=".version"

# 帮助信息
show_help() {
    echo "Media Packer 一键安装脚本 v$SCRIPT_VERSION"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --path PATH     安装目录 (默认: $HOME/media-packer)"
    echo "  --simple        只安装简化版依赖 (默认)"
    echo "  --full          安装完整版依赖"
    echo "  --quiet         静默安装"
    echo "  --no-symlink    不创建系统命令链接"
    echo "  --skip-deps     跳过依赖安装"
    echo "  --update        更新模式，保留配置文件"
    echo "  --force         强制安装，覆盖现有版本"
    echo "  --no-backup     不备份旧版本"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --path /opt/media-packer"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --full --quiet"
    echo ""
    echo "覆盖安装:"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --force"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --update"
}

# 打印带颜色的信息
print_info() {
    if [ "$QUIET" != "true" ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# 显示横幅
show_banner() {
    if [ "$QUIET" != "true" ]; then
        echo -e "${CYAN}"
        echo "╭─────────────────────────────────────────────────╮"
        echo "│            Media Packer 一键安装器             │"
        echo "│              VPS/本地环境适配版                 │"
        echo "│              版本: v$SCRIPT_VERSION                     │"
        echo "╰─────────────────────────────────────────────────╯"
        echo -e "${NC}"
    fi
}

# 检测系统环境
detect_system() {
    print_info "检测系统环境..."
    
    # 检测操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            VERSION=$VERSION_ID
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    print_info "检测到系统: $DISTRO"
    
    # 检测Python版本
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_info "Python版本: $PYTHON_VERSION"
        
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python版本检查通过"
        else
            print_error "需要Python 3.8或更高版本"
            install_python
        fi
    else
        print_error "未找到Python3"
        install_python
    fi
    
    # 检测pip
    if ! command -v pip3 >/dev/null 2>&1; then
        print_warning "未找到pip3，尝试安装..."
        install_pip
    fi
}

# 安装Python (如果需要)
install_python() {
    print_info "安装Python 3.8+..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        centos|rhel|fedora)
            if command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y python3 python3-pip
            else
                sudo yum install -y python3 python3-pip
            fi
            ;;
        macos)
            if command -v brew >/dev/null 2>&1; then
                brew install python3
            else
                print_error "请先安装Homebrew或手动安装Python 3.8+"
                exit 1
            fi
            ;;
        *)
            print_error "不支持的系统，请手动安装Python 3.8+"
            exit 1
            ;;
    esac
}

# 安装pip (如果需要)
install_pip() {
    case $DISTRO in
        ubuntu|debian)
            sudo apt install -y python3-pip
            ;;
        centos|rhel|fedora)
            if command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y python3-pip
            else
                sudo yum install -y python3-pip
            fi
            ;;
        macos)
            print_warning "在MacOS上，请使用brew安装Python3，它会自动包含pip"
            ;;
    esac
}

# 检测现有安装
check_existing_installation() {
    if [ -d "$INSTALL_DIR" ]; then
        print_info "检测到现有安装: $INSTALL_DIR"
        
        # 检查是否是完整的安装（包含必要的文件）
        local is_complete_install=true
        local required_files=("start.py" "media_packer_simple.py" "install_deps.py")
        
        for file in "${required_files[@]}"; do
            if [ ! -f "$INSTALL_DIR/$file" ]; then
                is_complete_install=false
                break
            fi
        done
        
        # 如果不是完整安装，当作新安装处理
        if [ "$is_complete_install" = "false" ]; then
            print_warning "检测到不完整的安装，将进行全新安装"
            print_info "首次安装到: $INSTALL_DIR"
            # 清理不完整的安装目录
            rm -rf "$INSTALL_DIR" 2>/dev/null || true
            return 1
        fi
        
        # 检查版本文件
        if [ -f "$INSTALL_DIR/$VERSION_FILE" ]; then
            OLD_VERSION=$(cat "$INSTALL_DIR/$VERSION_FILE" 2>/dev/null || echo "未知")
            print_info "当前版本: $OLD_VERSION"
            print_info "新版本: $SCRIPT_VERSION"
            
            if [ "$OLD_VERSION" = "$SCRIPT_VERSION" ] && [ "$FORCE_INSTALL" != "true" ]; then
                print_success "已安装最新版本 $SCRIPT_VERSION"
                if [ "$QUIET" != "true" ]; then
                    echo "使用 --force 参数强制重新安装"
                fi
                exit 0
            fi
        else
            print_warning "未找到版本信息，可能是旧版本安装"
            OLD_VERSION="旧版本"
        fi
        
        # 询问是否继续（除非是强制或静默模式）
        if [ "$FORCE_INSTALL" != "true" ] && [ "$QUIET" != "true" ]; then
            echo ""
            echo "发现现有安装:"
            echo "  位置: $INSTALL_DIR"
            echo "  当前版本: $OLD_VERSION"
            echo "  新版本: $SCRIPT_VERSION"
            echo ""
            
            # 检测是否在管道模式下运行
            if [ -t 0 ]; then
                # 交互模式 - 可以接收用户输入
                read -p "是否继续安装？(y/N): " -n 1 -r
                echo ""
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    print_info "安装已取消"
                    exit 0
                fi
            else
                # 管道模式 - 自动继续安装
                print_warning "检测到管道模式，将自动覆盖安装"
                print_info "如需取消，请使用 Ctrl+C"
                sleep 3
            fi
        fi
        
        return 0
    else
        print_info "首次安装到: $INSTALL_DIR"
        return 1
    fi
}

# 备份现有安装
backup_existing() {
    if [ ! -d "$INSTALL_DIR" ] || [ "$BACKUP_OLD" != "true" ]; then
        return
    fi
    
    local backup_dir="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    print_info "备份现有安装到: $backup_dir"
    
    if cp -r "$INSTALL_DIR" "$backup_dir"; then
        print_success "备份完成"
        echo "# 备份信息" > "$backup_dir/backup_info.txt"
        echo "备份时间: $(date)" >> "$backup_dir/backup_info.txt"
        echo "原版本: $(cat "$INSTALL_DIR/$VERSION_FILE" 2>/dev/null || echo "未知")" >> "$backup_dir/backup_info.txt"
        echo "新版本: $SCRIPT_VERSION" >> "$backup_dir/backup_info.txt"
    else
        print_warning "备份失败，继续安装..."
    fi
}

# 创建/准备安装目录
create_install_dir() {
    # 如果是更新模式，保留配置文件
    local config_backup=""
    if [ "$UPDATE_MODE" = "true" ] && [ -f "$INSTALL_DIR/config.json" ]; then
        config_backup=$(mktemp)
        cp "$INSTALL_DIR/config.json" "$config_backup"
        print_info "保留现有配置文件"
    fi
    
    print_info "准备安装目录: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # 恢复配置文件
    if [ -n "$config_backup" ] && [ -f "$config_backup" ]; then
        cp "$config_backup" "$INSTALL_DIR/config.json"
        rm -f "$config_backup"
        print_info "已恢复配置文件"
    fi
}

# 下载项目文件
download_files() {
    print_info "下载Media Packer核心文件..."
    local FILES=(
        "media_packer_simple.py"
        "start.py"
        "requirements.txt"
        "install_deps.py"
    )
    
    # 如果是完整版，额外下载完整版文件
    if [ "$MODE" = "full" ]; then
        FILES+=("media_packer_all_in_one.py")
    fi
    
    # 这里使用实际的GitHub仓库地址
    BASE_URL="https://raw.githubusercontent.com/Yan-nian/media-packer/main"
    
    for file in "${FILES[@]}"; do
        print_info "下载 $file..."
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$BASE_URL/$file" -o "$file" || {
                print_error "下载 $file 失败"
                exit 1
            }
        elif command -v wget >/dev/null 2>&1; then
            wget -q "$BASE_URL/$file" -O "$file" || {
                print_error "下载 $file 失败"
                exit 1
            }
        else
            print_error "需要curl或wget来下载文件"
            exit 1
        fi
    done
    
    # 设置执行权限
    chmod +x *.py
    
    # 创建输出目录
    mkdir -p output
    
    # 写入版本文件
    echo "$SCRIPT_VERSION" > "$VERSION_FILE"
}

# 安装Python依赖
install_dependencies() {
    if [ "$SKIP_DEPS" = "true" ]; then
        print_info "跳过依赖安装"
        return
    fi
    
    print_info "安装Python依赖..."
    
    # 先尝试使用我们自己的Python安装脚本
    if [ -f "install_deps.py" ]; then
        print_info "使用内部安装脚本安装依赖..."
        if python3 install_deps.py --mode "$MODE"; then
            print_success "依赖安装成功"
            return
        else
            print_warning "内部安装脚本失败，回退到传统方法"
        fi
    fi
    
    # 传统依赖安装方法
    if [ "$MODE" = "full" ]; then
        DEPS="torf click rich psutil requests tmdbv3api pymediainfo"
        print_info "安装完整版依赖..."
    else
        DEPS="torf click rich psutil"
        print_info "安装简化版依赖..."
    fi
    
    # 尝试不同的安装方式
    install_success=false
    
    # 方法1: 尝试普通用户安装
    if python3 -m pip install --user $DEPS >/dev/null 2>&1; then
        print_success "依赖安装成功（用户模式）"
        install_success=true
    # 方法2: 尝试break-system-packages（针对现代Python限制）
    elif python3 -m pip install --user --break-system-packages $DEPS >/dev/null 2>&1; then
        print_success "依赖安装成功（系统包模式）"
        install_success=true
    # 方法3: 尝试系统包管理器
    elif [ "$install_success" = "false" ]; then
        print_warning "pip安装失败，尝试系统包管理器..."
        case $DISTRO in
            ubuntu|debian)
                if sudo apt update && sudo apt install -y python3-torf python3-click python3-rich python3-psutil >/dev/null 2>&1; then
                    print_success "依赖安装成功（系统包）"
                    install_success=true
                fi
                ;;
        esac
    fi
    
    # 方法4: 最后尝试虚拟环境（但不设置为默认）
    if [ "$install_success" = "false" ]; then
        print_warning "创建虚拟环境..."
        if python3 -m venv venv && source venv/bin/activate && python3 -m pip install $DEPS; then
            print_success "依赖安装成功（虚拟环境）"
            # 创建激活虚拟环境的提示文件
            echo "# 注意：此安装使用了虚拟环境" > venv_info.txt
            echo "# 运行前需要激活：source venv/bin/activate" >> venv_info.txt
            install_success=true
        fi
    fi
    
    if [ "$install_success" = "false" ]; then
        print_error "依赖安装失败，请手动安装："
        print_error "python3 -m pip install --user $DEPS"
        exit 1
    fi
}

# 创建系统命令链接
create_symlinks() {
    if [ "$CREATE_SYMLINK" != "true" ]; then
        return
    fi
    
    print_info "创建启动命令..."
    
    # 创建智能启动脚本
    cat > media-packer << 'EOF'
#!/bin/bash
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$INSTALL_DIR"

# 检查是否有虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 直接运行简化版，避免交互
python3 media_packer_simple.py "$@"
EOF
    
    chmod +x media-packer
    
    # 尝试创建系统链接
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$INSTALL_DIR/media-packer" /usr/local/bin/media-packer
        print_success "创建系统命令: media-packer"
    elif command -v sudo >/dev/null 2>&1; then
        sudo ln -sf "$INSTALL_DIR/media-packer" /usr/local/bin/media-packer 2>/dev/null && {
            print_success "创建系统命令: media-packer"
        } || {
            print_warning "无法创建系统命令链接，请手动添加到PATH: $INSTALL_DIR"
        }
    else
        print_warning "无法创建系统命令链接，请手动添加到PATH: $INSTALL_DIR"
    fi
}

# 创建配置文件
create_config() {
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
}

# 运行测试
run_test() {
    print_info "运行功能测试..."
    
    # 如果有虚拟环境，先激活
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # 测试简化版程序
    if python3 media_packer_simple.py --help >/dev/null 2>&1; then
        print_success "功能测试通过"
    else
        print_error "功能测试失败，请检查依赖安装"
        exit 1
    fi
}

# 显示安装完成信息
show_completion() {
    print_success "Media Packer 安装完成！"
    echo ""
    echo -e "${CYAN}安装位置:${NC} $INSTALL_DIR"
    echo -e "${CYAN}配置文件:${NC} $INSTALL_DIR/config.json"
    echo ""
    echo -e "${GREEN}使用方法:${NC}"
    
    if [ "$CREATE_SYMLINK" = "true" ] && [ -f "/usr/local/bin/media-packer" ]; then
        echo "  media-packer pack /path/to/video.mkv     # 直接制种"
        echo "  media-packer batch /path/to/videos/*     # 批量制种"
        echo "  media-packer interactive                 # 交互界面"
    else
        echo "  cd $INSTALL_DIR"
        echo "  ./media-packer pack /path/to/video.mkv   # 直接制种"
        echo "  python3 media_packer_simple.py --help    # 查看帮助"
    fi
    
    echo ""
    echo -e "${YELLOW}提示:${NC}"
    echo "  • 已启用智能性能优化（自动CPU线程检测）"
    echo "  • 支持自动Piece Size选择和系统负载监控"
    echo "  • 精简安装，仅包含核心功能文件"
    
    if [ -f "venv_info.txt" ]; then
        echo "  • 使用了虚拟环境，运行时会自动激活"
    fi
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --path)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --simple)
                MODE="simple"
                shift
                ;;
            --full)
                MODE="full"
                shift
                ;;
            --quiet)
                QUIET=true
                shift
                ;;
            --no-symlink)
                CREATE_SYMLINK=false
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --update)
                UPDATE_MODE=true
                shift
                ;;
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            --no-backup)
                BACKUP_OLD=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 主函数
main() {
    parse_args "$@"
    
    show_banner
    
    detect_system
    check_existing_installation
    backup_existing
    create_install_dir
    download_files
    install_dependencies
    create_config
    create_symlinks
    run_test
    show_completion
}

# 运行主函数
main "$@"