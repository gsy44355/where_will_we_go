#!/bin/bash
# Web服务启动脚本

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查是否安装了依赖
if ! python3 -c "import flask" &> /dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "警告: 未找到.env文件，将使用默认配置"
    echo "建议创建.env文件并配置以下变量："
    echo "  AMAP_API_KEY=your_api_key"
    echo "  WEB_USERNAME=admin"
    echo "  WEB_PASSWORD=your_password"
    echo "  SECRET_KEY=your_secret_key"
    echo ""
fi

# 启动服务
echo "启动Web服务..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

python3 app.py

