# 部署指南

**版本**：v1.0
**最后更新**：2026-03-05

---

## 1. 开发环境搭建

### 1.1 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd where_will_we_go

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 1.2 配置

```bash
# 复制示例配置（如有 .env.example）
cp .env.example .env

# 编辑 .env，填写高德 API 密钥
# 至少需要配置 AMAP_API_KEY
```

### 1.3 启动开发服务器

```bash
# 方式一：Web 服务
python app.py
# 默认监听 http://0.0.0.0:5002

# 方式二：CLI 使用
python main.py --city "深圳" --brands "优衣库,海底捞" --threshold 200 --output json,log,html
```

---

## 2. 生产环境部署

### 2.1 安装 gunicorn

```bash
pip install gunicorn
```

### 2.2 使用启动脚本

```bash
chmod +x start_production.sh
./start_production.sh
```

启动脚本行为：
1. 检查 gunicorn 是否安装
2. 加载 `.env` 环境变量
3. 优先使用 `gunicorn.conf.py` 配置文件
4. 否则使用命令行参数启动

### 2.3 gunicorn 配置

**配置文件**：`gunicorn.conf.py`

| 参数 | 值 | 说明 |
|------|-----|------|
| `bind` | `0.0.0.0:$PORT` | 监听地址（默认 5002） |
| `workers` | `CPU*2+1` | 工作进程数 |
| `worker_class` | `sync` | 同步 worker |
| `timeout` | `120` | 请求超时（秒） |
| `keepalive` | `5` | Keep-alive 超时 |
| `preload_app` | `True` | 预加载应用（共享内存） |
| `max_requests` | `1000` | 每个 worker 最大请求数（自动重启） |
| `max_requests_jitter` | `50` | 最大请求数随机抖动 |
| `graceful_timeout` | `30` | 优雅关闭超时 |

**日志配置**：
- `accesslog` / `errorlog` → 标准输出/标准错误
- `loglevel` → `info`
- 访问日志格式含响应时间 `%(D)s`

**安全限制**：
- `limit_request_line` = 4094
- `limit_request_fields` = 100
- `limit_request_field_size` = 8190

### 2.4 注意事项

- SSE 流式响应需要 `sync` worker 类型（不能用 `gevent`/`eventlet`）
- `timeout=120` 考虑了搜索+聚类可能耗时较长
- `preload_app=True` 减少内存使用但代码更新需重启

---

## 3. Systemd 服务配置

### 3.1 安装步骤

```bash
# 1. 编辑配置文件
sudo cp cluster-finder.service.example /etc/systemd/system/cluster-finder.service
sudo vim /etc/systemd/system/cluster-finder.service
# 修改 User, Group, WorkingDirectory, ExecStart

# 2. 重载 systemd
sudo systemctl daemon-reload

# 3. 启用开机自启
sudo systemctl enable cluster-finder

# 4. 启动服务
sudo systemctl start cluster-finder
```

### 3.2 服务配置要点

```ini
[Unit]
Description=商圈查找Web服务
After=network.target

[Service]
Type=notify
User=your_user
Group=your_group
WorkingDirectory=/path/to/where_will_we_go
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn.conf.py app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 3.3 常用命令

```bash
sudo systemctl status cluster-finder     # 查看状态
sudo systemctl stop cluster-finder       # 停止
sudo systemctl restart cluster-finder    # 重启
sudo journalctl -u cluster-finder -f     # 查看日志
```

---

## 4. uTools 插件部署

### 4.1 纯前端模式（推荐）

uTools 插件默认以纯前端方式运行，直接在浏览器环境中调用高德 REST API，无需后端。

**安装步骤**：
1. 打开 uTools → 插件开发
2. 将 `utools_plugin/` 目录导入
3. 在插件中配置高德 API Key

**API Key 存储**：
- uTools 环境：`utools.dbStorage.getItem('amap_api_key')`
- 降级方案：`localStorage.getItem('amap_api_key')`

### 4.2 后端模式（可选）

若需要后端功能（门店去重、优化算法等），可启动可选后端：

```bash
cd utools_plugin
pip install -r requirements.txt
python server.py
# 监听 http://127.0.0.1:8765
```

---

## 5. 目录结构

```
where_will_we_go/
├── .env                           # 环境配置（不提交到 git）
├── .env.example                   # 配置模板
├── requirements.txt               # Python 依赖
├── config.py                      # 配置加载
├── main.py                        # CLI 入口
├── app.py                         # Flask Web 入口
├── amap_api.py                    # 高德 API 封装
├── cluster_finder.py              # 聚类入口
├── cluster_finder_optimized.py    # 优化聚类算法
├── distance.py                    # 距离计算
├── output.py                      # 结果输出
├── log_capture.py                 # 日志捕获
├── gunicorn.conf.py               # gunicorn 配置
├── start_production.sh            # 生产启动脚本
├── cluster-finder.service.example # systemd 服务模板
├── templates/                     # Flask 模板
│   ├── login.html
│   ├── search.html
│   ├── result.html
│   └── map_view.html
├── results/                       # 搜索结果存储（自动创建）
├── utools_plugin/                 # uTools 桌面插件
│   ├── plugin.json
│   ├── preload.js
│   ├── index.html
│   ├── distance.js
│   ├── amap_api.js
│   ├── cluster_finder.js
│   ├── output.js
│   ├── server.py
│   ├── requirements.txt
│   ├── logo.png
│   └── README.md
├── CLAUDE.md                      # Claude Code 项目说明
└── SDD-docs/                      # SDD 文档目录
```

---

## 6. 健康检查

### 6.1 服务可用性

```bash
# 检查服务是否响应
curl -s http://localhost:5002/ -o /dev/null -w "%{http_code}"
# 应返回 302 (重定向到登录)
```

### 6.2 API Key 验证

```bash
# 通过 CLI 快速验证 API Key 是否有效
python -c "
from amap_api import search_poi
stores = search_poi('深圳', '星巴克', max_pages=1)
print(f'找到 {len(stores)} 个门店')
"
```

---

## 7. 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 地图不显示 | 缺少 JS API Key 或安全密钥 | 配置 `AMAP_JS_KEY` 和 `AMAP_SECURITY_CODE` |
| POI 搜索返回空 | API Key 类型错误 | 确保使用"Web 服务"类型 Key |
| 频繁限流 | 请求过快 | 提高 `REQUEST_DELAY` |
| SSE 超时断开 | gunicorn timeout 过短 | 增大 `timeout` 值 |
| 内存占用高 | 大量门店组合 | 使用优化算法、减少品牌数 |
