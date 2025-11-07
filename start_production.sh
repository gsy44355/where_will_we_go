#!/bin/bash
# 生产环境启动脚本
# 使用 gunicorn 作为 WSGI 服务器

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查是否安装了gunicorn
if ! python3 -c "import gunicorn" &> /dev/null; then
    echo "错误: 未安装 gunicorn"
    echo "请运行: pip install gunicorn"
    exit 1
fi

# 读取环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 设置默认值
PORT=${PORT:-5002}
WORKERS=${WORKERS:-4}
BIND_ADDR="0.0.0.0:${PORT}"

# 检查配置文件是否存在
if [ -f gunicorn.conf.py ]; then
    echo "使用配置文件: gunicorn.conf.py"
    gunicorn -c gunicorn.conf.py app:app
else
    echo "使用命令行参数启动..."
    echo "监听地址: ${BIND_ADDR}"
    echo "工作进程数: ${WORKERS}"
    echo ""
    gunicorn \
        --bind "${BIND_ADDR}" \
        --workers "${WORKERS}" \
        --worker-class sync \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        app:app
fi

