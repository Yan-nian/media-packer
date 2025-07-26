#!/bin/bash

# Media Packer 通用一键安装脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 项目信息
PROJECT_NAME="Media Packer"
GITHUB_RAW="https://raw.githubusercontent.com/Yan-nian/media-packer/main"
INSTALL_DIR="$HOME/.media-packer"
VERSION="2.0.0"

# 打印函数
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "${CYAN}[HEADER]${NC} $1"; }

# 显示安装选项
show_install_options() {
    echo -e "${CYAN}${BOLD}选择安装模式：${NC}"
    echo
    echo "1) 🚀 快速安装（推荐） - 自动选择最佳方式"
    echo "2) 🎯 简化版安装      - 仅安装核心功能"
    echo "3) 📦 完整版安装      - 安装所有功能"
    echo "4) 🔧 自定义安装      - 手动选择配置"
    echo "5) 🔍 系统检查        - 仅检查环境，不安装"
    echo
    
    if [ "$QUIET_MODE" != true ]; then
        read -p "请选择 (1-5, 默认1): " choice
        case $choice in
            2) INSTALL_MODE="simple" ;;
            3) INSTALL_MODE="full" ;;
            4) INSTALL_MODE="custom" ;;
            5) INSTALL_MODE="check" ;;
            *) INSTALL_MODE="auto" ;;
        esac
    else
        INSTALL_MODE="auto"
    fi
    
    print_info "选择的安装模式: $INSTALL_MODE"
}

# 自定义安装选项
custom_install_options() {
    echo -e "${CYAN}${BOLD}自定义安装配置：${NC}"
    echo
    
    # 选择安装路径
    echo -e "${YELLOW}1. 安装路径：${NC}"
    echo "   默认: $HOME/.media-packer"
    read -p "   自定义路径 (回车使用默认): " custom_path
    if [ -n "$custom_path" ]; then
        INSTALL_DIR="$custom_path"
    fi
    
    # 选择Python版本
    echo -e "${YELLOW}2. Python版本：${NC}"
    available_pythons=()
    for py_cmd in python3.11 python3.10 python3.9 python3.8 python3; do
        if command -v "$py_cmd" &> /dev/null; then
            version=$($py_cmd --version 2>&1 | cut -d' ' -f2)
            available_pythons+=("$py_cmd:$version")
            echo "   $(( ${#available_pythons[@]} ))) $py_cmd ($version)"
        fi
    done
    
    if [ ${#available_pythons[@]} -gt 1 ]; then
        read -p "   选择Python版本 (1-${#available_pythons[@]}, 默认1): " py_choice
        if [ -n "$py_choice" ] && [ "$py_choice" -ge 1 ] && [ "$py_choice" -le ${#available_pythons[@]} ]; then
            selected_python=$(echo "${available_pythons[$((py_choice-1))]}" | cut -d':' -f1)
            PYTHON_CMD="$selected_python"
        fi
    fi
    
    # 选择安装方式
    echo -e "${YELLOW}3. 依赖安装方式：${NC}"
    echo "   1) 自动选择 (推荐)"
    echo "   2) 虚拟环境"
    echo "   3) 用户安装"
    echo "   4) 系统安装"
    read -p "   选择安装方式 (1-4, 默认1): " install_method
    case $install_method in
        2) PREFERRED_INSTALL="venv" ;;
        3) PREFERRED_INSTALL="user" ;;
        4) PREFERRED_INSTALL="system" ;;
        *) PREFERRED_INSTALL="auto" ;;
    esac
    
    # 是否创建快捷方式
    if [[ "$OS" == "linux" ]]; then
        read -p "4. 是否创建桌面快捷方式？(y/N): " create_shortcut
        if [[ $create_shortcut =~ ^[Yy]$ ]]; then
            CREATE_SHORTCUT=true
        fi
    fi
}
show_welcome() {
    clear
    echo -e "${GREEN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Media Packer v$VERSION                        ║"
    echo "║                   通用一键安装脚本                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${CYAN}🚀 一个专门为PT站用户设计的轻量级种子制作工具${NC}"
    echo -e "${CYAN}📦 无需Git，无需仓库，一键安装所有功能${NC}"
    echo
}

# 检测操作系统
detect_system() {
    print_header "检测系统环境"
    
    # 检测操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt &> /dev/null; then
            DISTRO="debian"
            DISTRO_NAME="Ubuntu/Debian"
        elif command -v yum &> /dev/null; then
            DISTRO="redhat"
            DISTRO_NAME="CentOS/RHEL"
        elif command -v dnf &> /dev/null; then
            DISTRO="fedora"
            DISTRO_NAME="Fedora"
        elif command -v pacman &> /dev/null; then
            DISTRO="arch"
            DISTRO_NAME="Arch Linux"
        else
            DISTRO="unknown"
            DISTRO_NAME="Unknown Linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
        DISTRO_NAME="macOS"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        DISTRO="windows"
        DISTRO_NAME="Windows (WSL/Cygwin)"
    else
        OS="unknown"
        DISTRO="unknown"
        DISTRO_NAME="Unknown OS"
    fi
    
    print_info "检测到系统: $DISTRO_NAME"
    
    # 检测架构
    ARCH=$(uname -m)
    print_info "系统架构: $ARCH"
    
    # 检测是否为root用户
    if [ "$EUID" -eq 0 ]; then
        print_warning "检测到root用户，建议使用普通用户运行"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查网络连接
check_network() {
    print_info "检查网络连接..."
    
    if command -v curl &> /dev/null; then
        if curl -s --max-time 10 --head "$GITHUB_RAW/README.md" > /dev/null 2>&1; then
            print_success "网络连接正常"
        else
            print_error "无法连接到GitHub，请检查网络或使用代理"
            exit 1
        fi
    elif command -v wget &> /dev/null; then
        if wget -q --timeout=10 --spider "$GITHUB_RAW/README.md" > /dev/null 2>&1; then
            print_success "网络连接正常"
        else
            print_error "无法连接到GitHub，请检查网络或使用代理"
            exit 1
        fi
    else
        print_error "未找到curl或wget，无法下载文件"
        install_basic_tools
    fi
}

# 安装基本工具
install_basic_tools() {
    print_info "安装基本工具..."
    
    case $DISTRO in
        "debian")
            sudo apt update -qq
            sudo apt install -y curl wget python3 python3-pip python3-venv
            ;;
        "redhat")
            sudo yum install -y curl wget python3 python3-pip
            ;;
        "fedora")
            sudo dnf install -y curl wget python3 python3-pip
            ;;
        "arch")
            sudo pacman -S --noconfirm curl wget python python-pip
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install curl wget python3
            else
                print_error "请先安装Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
            ;;
        *)
            print_error "不支持的系统，请手动安装curl、wget、python3"
            exit 1
            ;;
    esac
    
    print_success "基本工具安装完成"
}

# 检查Python环境
check_python() {
    print_info "检查Python环境..."
    
    # 查找可用的Python
    for py_cmd in python3.11 python3.10 python3.9 python3.8 python3 python; do
        if command -v "$py_cmd" &> /dev/null; then
            PYTHON_VERSION=$($py_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
            PYTHON_VERSION_NUM=$($py_cmd -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)" 2>/dev/null || echo "0")
            
            if [ "$PYTHON_VERSION_NUM" -ge 38 ]; then
                PYTHON_CMD="$py_cmd"
                print_success "找到Python $PYTHON_VERSION: $py_cmd"
                return 0
            fi
        fi
    done
    
    # 如果没找到合适的Python，尝试安装
    print_warning "未找到Python 3.8+，尝试安装..."
    install_python
}

# 安装Python
install_python() {
    case $DISTRO in
        "debian")
            sudo apt update -qq
            sudo apt install -y python3.9 python3.9-pip python3.9-venv || \
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        "redhat")
            sudo yum install -y python39 python39-pip || \
            sudo yum install -y python3 python3-pip
            ;;
        "fedora")
            sudo dnf install -y python3 python3-pip
            ;;
        "arch")
            sudo pacman -S --noconfirm python python-pip
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install python3
            else
                print_error "请安装Homebrew后重试"
                exit 1
            fi
            ;;
        *)
            print_error "无法自动安装Python，请手动安装Python 3.8+"
            exit 1
            ;;
    esac
    
    # 重新检查Python
    check_python
}

# 创建安装目录
create_install_dir() {
    print_info "创建安装目录..."
    
    # 删除旧安装（如果存在）
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "发现现有安装，是否覆盖？"
        read -p "覆盖现有安装？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            print_info "已删除旧安装"
        else
            print_info "保留现有安装，仅更新文件"
        fi
    fi
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    print_success "安装目录: $INSTALL_DIR"
}

# 下载项目文件
download_files() {
    print_header "下载项目文件"
    
    # 根据安装模式确定需要下载的文件
    if [ "$INSTALL_MODE" = "simple" ]; then
        files=(
            "media_packer_simple.py:简化版主程序"
            "install_deps.py:依赖管理工具"
            "requirements.txt:依赖列表"
        )
    elif [ "$INSTALL_MODE" = "full" ]; then
        files=(
            "media_packer_simple.py:简化版主程序"
            "media_packer_all_in_one.py:完整版主程序"
            "install_deps.py:依赖管理工具"
            "requirements.txt:依赖列表"
        )
    elif [ "$INSTALL_MODE" = "check" ]; then
        # 仅检查模式，不下载文件
        print_info "仅检查模式，跳过文件下载"
        return 0
    else
        # 默认下载所有核心文件
        files=(
            "media_packer_simple.py:简化版主程序"
            "media_packer_all_in_one.py:完整版主程序"
            "install_deps.py:依赖管理工具"
            "requirements.txt:依赖列表"
        )
    fi
    
    # 下载文件
    for file_info in "${files[@]}"; do
        file=$(echo "$file_info" | cut -d':' -f1)
        desc=$(echo "$file_info" | cut -d':' -f2)
        
        print_info "下载 $desc..."
        if command -v curl &> /dev/null; then
            curl -fsSL "$GITHUB_RAW/$file" -o "$file" || {
                print_error "下载 $file 失败"
                exit 1
            }
        else
            wget -q "$GITHUB_RAW/$file" -O "$file" || {
                print_error "下载 $file 失败"
                exit 1
            }
        fi
    done
    
    # 设置执行权限
    chmod +x *.py 2>/dev/null || true
    
    print_success "文件下载完成"
}

# 智能安装依赖
install_dependencies() {
    print_header "安装Python依赖"
    
    # 根据安装模式确定需要的包
    case $INSTALL_MODE in
        "simple")
            REQUIRED_PACKAGES="torf click rich"
            ;;
        "full")
            REQUIRED_PACKAGES="torf click rich pymediainfo tmdbv3api requests"
            ;;
        *)
            REQUIRED_PACKAGES="torf click rich"
            ;;
    esac
    
    print_info "需要安装的包: $REQUIRED_PACKAGES"
    
    # 检查依赖是否已安装
    packages_installed=true
    for pkg in $REQUIRED_PACKAGES; do
        if ! $PYTHON_CMD -c "import $pkg" 2>/dev/null; then
            packages_installed=false
            break
        fi
    done
    
    if [ "$packages_installed" = true ]; then
        print_success "所需依赖已安装"
        return 0
    fi
    
    print_info "安装依赖包..."
    
    # 根据首选方式或自动选择安装方法
    if [ "$PREFERRED_INSTALL" = "venv" ]; then
        create_virtual_env
        return $?
    elif [ "$PREFERRED_INSTALL" = "user" ]; then
        install_user_packages
        return $?
    elif [ "$PREFERRED_INSTALL" = "system" ]; then
        install_system_packages
        return $?
    else
        # 自动选择最佳安装方式
        install_methods=(
            "user:用户安装模式"
            "user_break:用户安装+break-system-packages"
            "venv:虚拟环境模式"
            "system:系统包模式"
        )
        
        for method_info in "${install_methods[@]}"; do
            method=$(echo "$method_info" | cut -d':' -f1)
            desc=$(echo "$method_info" | cut -d':' -f2)
            
            print_info "尝试 $desc..."
            
            case $method in
                "user")
                    if install_user_packages; then
                        print_success "用户安装模式成功"
                        return 0
                    fi
                    ;;
                "user_break")
                    if $PYTHON_CMD -m pip install --user --break-system-packages $REQUIRED_PACKAGES 2>/dev/null; then
                        print_success "用户安装+break-system-packages成功"
                        return 0
                    fi
                    ;;
                "venv")
                    if create_virtual_env; then
                        return 0
                    fi
                    ;;
                "system")
                    if install_system_packages; then
                        return 0
                    fi
                    ;;
            esac
        done
    fi
    
    print_error "所有安装方法都失败了"
    show_manual_install_guide
    exit 1
}

# 安装用户包
install_user_packages() {
    if $PYTHON_CMD -m pip install --user $REQUIRED_PACKAGES 2>/dev/null; then
        print_success "用户安装模式成功"
        return 0
    else
        return 1
    fi
}

# 创建虚拟环境
create_virtual_env() {
    print_info "创建虚拟环境..."
    VENV_PATH="$INSTALL_DIR/venv"
    
    if $PYTHON_CMD -m venv "$VENV_PATH" 2>/dev/null; then
        print_success "虚拟环境创建成功"
        
        # 激活虚拟环境并安装依赖
        source "$VENV_PATH/bin/activate"
        pip install --upgrade pip
        pip install $REQUIRED_PACKAGES
        deactivate
        
        # 更新Python命令
        PYTHON_CMD="$VENV_PATH/bin/python"
        USE_VENV=true
        print_success "虚拟环境依赖安装完成"
        return 0
    else
        print_warning "虚拟环境创建失败"
        return 1
    fi
}

# 安装系统包
install_system_packages() {
    print_info "尝试安装系统Python包..."
    
    case $DISTRO in
        "debian")
            if sudo apt install -y python3-pip python3-venv 2>/dev/null; then
                install_user_packages
                return $?
            fi
            ;;
        "redhat"|"fedora")
            if sudo yum install -y python3-pip 2>/dev/null || sudo dnf install -y python3-pip 2>/dev/null; then
                install_user_packages
                return $?
            fi
            ;;
    esac
    
    return 1
}

# 显示手动安装指南
show_manual_install_guide() {
    echo -e "${RED}${BOLD}自动安装失败，请手动安装依赖：${NC}"
    echo
    echo -e "${YELLOW}方法1: 虚拟环境（推荐）${NC}"
    echo "cd $INSTALL_DIR"
    echo "$PYTHON_CMD -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install torf click rich"
    echo
    echo -e "${YELLOW}方法2: 强制用户安装${NC}"
    echo "$PYTHON_CMD -m pip install --user --break-system-packages torf click rich"
    echo
    echo -e "${YELLOW}方法3: 系统包管理器${NC}"
    case $DISTRO in
        "debian")
            echo "sudo apt install python3-pip python3-venv"
            ;;
        "redhat")
            echo "sudo yum install python3-pip"
            ;;
        "fedora")
            echo "sudo dnf install python3-pip"
            ;;
    esac
}

# 创建启动脚本
create_launchers() {
    print_header "创建启动脚本"
    
    # 创建主启动脚本
    cat > media-packer << EOF
#!/bin/bash
# Media Packer 主启动脚本
SCRIPT_DIR="$INSTALL_DIR"
cd "\$SCRIPT_DIR"

# 检查虚拟环境
if [ -f "\$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_CMD="\$SCRIPT_DIR/venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到Python"
    exit 1
fi

# 默认使用简化版
\$PYTHON_CMD media_packer_simple.py "\$@"
EOF
    
    # 创建完整版启动脚本
    cat > media-packer-full << EOF
#!/bin/bash
# Media Packer 完整版启动脚本
SCRIPT_DIR="$INSTALL_DIR"
cd "\$SCRIPT_DIR"

if [ -f "\$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_CMD="\$SCRIPT_DIR/venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "错误: 未找到Python"
    exit 1
fi

\$PYTHON_CMD media_packer_all_in_one.py "\$@"
EOF
    
    # 创建依赖管理脚本
    cat > media-packer-deps << EOF
#!/bin/bash
# Media Packer 依赖管理脚本
SCRIPT_DIR="$INSTALL_DIR"
cd "\$SCRIPT_DIR"

if [ -f "\$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON_CMD="\$SCRIPT_DIR/venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "错误: 未找到Python"
    exit 1
fi

\$PYTHON_CMD install_deps.py "\$@"
EOF
    
    # 设置执行权限
    chmod +x media-packer media-packer-full media-packer-deps
    
    print_success "启动脚本创建完成"
}

# 配置PATH环境
setup_path() {
    print_info "配置环境变量..."
    
    # 检查是否已在PATH中
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        # 添加到各种shell配置文件
        shell_configs=(
            "$HOME/.bashrc"
            "$HOME/.zshrc"
            "$HOME/.profile"
        )
        
        for config in "${shell_configs[@]}"; do
            if [ -f "$config" ]; then
                if ! grep -q "media-packer" "$config"; then
                    echo "# Media Packer" >> "$config"
                    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$config"
                    print_info "已添加到 $config"
                fi
            fi
        done
        
        # 临时添加到当前session
        export PATH="$INSTALL_DIR:$PATH"
        
        print_success "环境变量配置完成"
    else
        print_info "环境变量已配置"
    fi
}

# 创建桌面快捷方式（可选）
create_desktop_shortcut() {
    if [[ "$OS" == "linux" && -d "$HOME/Desktop" && "$CREATE_SHORTCUT" = true ]]; then
        print_info "创建桌面快捷方式..."
        cat > "$HOME/Desktop/media-packer.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Packer
Comment=轻量级种子制作工具
Exec=$INSTALL_DIR/media-packer
Icon=applications-multimedia
Terminal=true
Categories=Multimedia;
EOF
        chmod +x "$HOME/Desktop/media-packer.desktop"
        print_success "桌面快捷方式已创建"
    fi
}

# 运行测试
run_tests() {
    print_header "运行安装测试"
    
    # 测试Python导入
    if $PYTHON_CMD -c "import torf, click, rich; print('✓ 所有依赖包导入成功')" 2>/dev/null; then
        print_success "依赖测试通过"
    else
        print_error "依赖测试失败"
        return 1
    fi
    
    # 测试程序启动
    if $PYTHON_CMD media_packer_simple.py --help > /dev/null 2>&1; then
        print_success "程序启动测试通过"
    else
        print_error "程序启动测试失败"
        return 1
    fi
    
    return 0
}

# 显示使用说明
show_usage_guide() {
    echo
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗"
    echo "║                        安装完成！                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${CYAN}📁 安装位置:${NC} $INSTALL_DIR"
    echo -e "${CYAN}🐍 Python版本:${NC} $PYTHON_VERSION ($PYTHON_CMD)"
    if [ "$USE_VENV" = true ]; then
        echo -e "${CYAN}🔧 运行环境:${NC} 虚拟环境"
    else
        echo -e "${CYAN}🔧 运行环境:${NC} 系统环境"
    fi
    echo
    echo -e "${YELLOW}${BOLD}使用方法：${NC}"
    echo
    echo -e "${GREEN}1. 直接使用命令（推荐）:${NC}"
    echo "   media-packer                    # 交互式使用"
    echo "   media-packer pack video.mkv    # 生成种子"
    echo "   media-packer-full               # 使用完整版"
    echo
    echo -e "${GREEN}2. 进入目录使用:${NC}"
    echo "   cd $INSTALL_DIR"
    echo "   $PYTHON_CMD media_packer_simple.py"
    echo
    echo -e "${GREEN}3. 命令行示例:${NC}"
    echo "   # 生成单个种子"
    echo "   media-packer pack /path/to/video.mkv --name 'My_Movie'"
    echo
    echo "   # 批量处理"
    echo "   media-packer batch /path/to/videos/* --organize"
    echo
    echo "   # 管理依赖"
    echo "   media-packer-deps --mode simple"
    echo
    echo -e "${BLUE}💡 提示:${NC}"
    echo "   - 如果命令不可用，请重新打开终端"
    echo "   - 使用 --help 查看详细帮助"
    echo "   - 简化版适合大多数用户，完整版包含高级功能"
    echo
    echo -e "${PURPLE}🔗 更多信息:${NC}"
    echo "   - GitHub: https://github.com/Yan-nian/media-packer"
    echo "   - Issues: https://github.com/Yan-nian/media-packer/issues"
    echo
}

# 清理函数
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "安装过程中发生错误"
        echo
        echo "常见解决方案："
        echo "1. 检查网络连接"
        echo "2. 确保有足够权限"
        echo "3. 手动安装Python依赖"
        echo "4. 查看错误日志"
        echo
        echo "获取帮助："
        echo "https://github.com/Yan-nian/media-packer/issues"
    fi
}

# 主函数
main() {
    # 设置错误处理
    trap cleanup EXIT
    
    # 检查参数
    case "${1:-}" in
        --help|-h)
            echo "Media Packer 通用一键安装脚本"
            echo "使用方法: curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash"
            echo
            echo "选项:"
            echo "  --help, -h        显示帮助"
            echo "  --quiet, -q       静默安装（自动选择默认选项）"
            echo "  --force, -f       强制重新安装"
            echo "  --simple          仅安装简化版"
            echo "  --full            安装完整版"
            echo "  --check           仅检查环境，不安装"
            echo "  --path PATH       指定安装路径"
            echo
            echo "示例:"
            echo "  # 默认安装"
            echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash"
            echo
            echo "  # 静默安装简化版"
            echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --quiet --simple"
            echo
            echo "  # 安装到指定目录"
            echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/universal-install.sh | bash -s -- --path /opt/media-packer"
            exit 0
            ;;
        --quiet|-q)
            QUIET_MODE=true
            shift
            ;;
        --force|-f)
            FORCE_INSTALL=true
            shift
            ;;
        --simple)
            INSTALL_MODE="simple"
            shift
            ;;
        --full)
            INSTALL_MODE="full"
            shift
            ;;
        --check)
            INSTALL_MODE="check"
            shift
            ;;
        --path)
            INSTALL_DIR="$2"
            shift 2
            ;;
    esac
    
    # 处理剩余参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quiet|-q)
                QUIET_MODE=true
                ;;
            --force|-f)
                FORCE_INSTALL=true
                ;;
            --simple)
                INSTALL_MODE="simple"
                ;;
            --full)
                INSTALL_MODE="full"
                ;;
            --check)
                INSTALL_MODE="check"
                ;;
            --path)
                INSTALL_DIR="$2"
                shift
                ;;
        esac
        shift
    done
    
    # 开始安装
    show_welcome
    detect_system
    check_network
    check_python
    
    # 根据模式选择安装流程
    if [ "$INSTALL_MODE" = "check" ]; then
        print_success "环境检查完成！"
        echo
        echo -e "${GREEN}系统信息：${NC}"
        echo -e "  操作系统: $DISTRO_NAME"
        echo -e "  Python版本: $PYTHON_VERSION ($PYTHON_CMD)"
        echo -e "  系统架构: $ARCH"
        echo
        exit 0
    elif [ "$QUIET_MODE" != true ] && [ -z "$INSTALL_MODE" ]; then
        show_install_options
    elif [ -z "$INSTALL_MODE" ]; then
        INSTALL_MODE="auto"
    fi
    
    # 自定义安装选项
    if [ "$INSTALL_MODE" = "custom" ]; then
        custom_install_options
    fi
    
    create_install_dir
    download_files
    
    # 跳过检查模式的后续步骤
    if [ "$INSTALL_MODE" != "check" ]; then
        install_dependencies
        create_launchers
        setup_path
        create_desktop_shortcut
        
        # 运行测试
        if run_tests; then
            show_usage_guide
            print_success "Media Packer 安装成功！"
        else
            print_error "安装测试失败，请检查配置"
            exit 1
        fi
    fi
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
