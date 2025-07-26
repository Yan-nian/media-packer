#!/bin/bash

# 简化的测试版本
echo "Script started..."

# 测试终端检测
if [ -t 0 ] && [ -t 1 ]; then
    echo "Interactive terminal detected"
else
    echo "Non-interactive environment detected"
fi

# 测试基本命令
echo "Testing system detection..."
uname -s

echo "Script completed."
