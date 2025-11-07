# Gunicorn配置文件
# 生产环境推荐使用此配置文件启动服务

import multiprocessing
import os

# 服务器配置
bind = f"0.0.0.0:{os.getenv('PORT', '5002')}"
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# 日志配置
accesslog = '-'  # 输出到标准输出
errorlog = '-'   # 输出到标准错误
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名称
proc_name = 'cluster-finder'

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 性能优化
preload_app = True
max_requests = 1000
max_requests_jitter = 50

# 优雅重启
graceful_timeout = 30

