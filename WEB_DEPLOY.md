# Web服务部署说明

## 功能特性

- ✅ 用户登录认证
- ✅ 移动端友好的响应式界面
- ✅ 商圈搜索功能
- ✅ 地图可视化展示（嵌入iframe）
- ✅ 结果列表展示

## 环境要求

- Python 3.7+
- 高德地图API密钥

## 安装步骤

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量（创建或编辑 `.env` 文件）：
```env
# 高德地图API密钥（必需）
AMAP_API_KEY=your_amap_api_key_here

# Web服务配置（可选）
SECRET_KEY=your-secret-key-change-this-in-production
WEB_USERNAME=admin
WEB_PASSWORD=admin123
PORT=5000
FLASK_DEBUG=False
DEFAULT_DISTANCE_THRESHOLD=200
```

## 启动服务

### ⚠️ 重要说明

**开发环境**：可以使用 `python app.py` 直接启动，方便调试。

**生产环境**：**不要使用** `python app.py`！应该使用专业的WSGI服务器（如gunicorn）来运行Flask应用。

### 开发模式

```bash
# 方式1: 使用启动脚本
./start_web.sh

# 方式2: 直接运行
python app.py
```

开发模式特点：
- 代码修改后自动重载
- 显示详细的错误信息
- 单进程运行，性能较低
- 仅适合本地开发

### 生产模式

#### 方式1: 使用生产启动脚本（推荐）

```bash
# 1. 安装gunicorn
pip install gunicorn

# 2. 使用生产启动脚本
./start_production.sh
```

启动脚本会自动：
- 检查gunicorn是否安装
- 读取 `.env` 文件中的配置
- 使用多进程模式运行（默认4个工作进程）
- 监听配置的端口（默认5002）

#### 方式2: 使用gunicorn命令行

```bash
# 安装gunicorn
pip install gunicorn

# 启动服务（4个工作进程，监听5002端口）
gunicorn --bind 0.0.0.0:5002 --workers 4 --timeout 120 app:app

# 或者使用配置文件
gunicorn -c gunicorn.conf.py app:app
```

#### 方式3: 使用systemd服务（最推荐，适合服务器部署）

**步骤1**: 安装gunicorn
```bash
pip install gunicorn
```

**步骤2**: 创建systemd服务文件

复制 `cluster-finder.service.example` 到 `/etc/systemd/system/cluster-finder.service`，并修改其中的路径：

```bash
sudo cp cluster-finder.service.example /etc/systemd/system/cluster-finder.service
sudo nano /etc/systemd/system/cluster-finder.service
```

需要修改的内容：
- `User=your_user` → 改为实际运行服务的用户
- `WorkingDirectory=/path/to/where_will_we_go` → 改为项目实际路径
- `ExecStart` → 改为实际的gunicorn路径

**步骤3**: 启动服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 设置开机自启
sudo systemctl enable cluster-finder

# 启动服务
sudo systemctl start cluster-finder

# 查看服务状态
sudo systemctl status cluster-finder

# 查看日志
sudo journalctl -u cluster-finder -f

# 停止服务
sudo systemctl stop cluster-finder

# 重启服务
sudo systemctl restart cluster-finder
```

### 生产环境配置建议

1. **工作进程数**：建议设置为 `CPU核心数 * 2 + 1`
   ```bash
   # 查看CPU核心数
   nproc
   
   # 设置工作进程数（在.env文件中）
   WORKERS=4
   ```

2. **端口配置**：在 `.env` 文件中设置
   ```env
   PORT=5002
   ```

3. **日志管理**：生产环境建议将日志输出到文件
   ```python
   # 在 gunicorn.conf.py 中修改
   accesslog = '/var/log/cluster-finder/access.log'
   errorlog = '/var/log/cluster-finder/error.log'
   ```

4. **使用反向代理**：生产环境强烈建议使用Nginx作为反向代理

## 访问服务

- 本地访问：http://localhost:5000
- 服务器访问：http://your-server-ip:5000

## 使用说明

1. 打开浏览器访问服务地址
2. 使用配置的用户名和密码登录（默认：admin/admin123）
3. 在搜索页面输入：
   - 城市名称（如：北京、上海、深圳）
   - 品牌列表（用逗号分隔，如：优衣库,海底捞,西塔老太太）
   - 距离阈值（默认200米）
4. 点击"开始搜索"
5. 查看搜索结果和地图

## 安全建议

1. **修改默认密码**：在生产环境中务必修改 `.env` 文件中的 `WEB_PASSWORD`
2. **使用强密钥**：修改 `SECRET_KEY` 为随机生成的强密钥
3. **使用HTTPS**：在生产环境中使用Nginx反向代理并配置SSL证书
4. **防火墙配置**：只开放必要的端口

## Nginx反向代理配置示例

生产环境强烈建议使用Nginx作为反向代理，可以提供：
- HTTPS支持
- 静态文件服务
- 负载均衡
- 更好的安全性

### 基本配置

创建 `/etc/nginx/sites-available/cluster-finder`：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名或IP

    # 日志配置
    access_log /var/log/nginx/cluster-finder-access.log;
    error_log /var/log/nginx/cluster-finder-error.log;

    # 客户端上传大小限制（如果需要）
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5002;  # 修改为实际端口
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/cluster-finder /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl reload nginx  # 重新加载配置
```

### HTTPS配置（推荐）

使用Let's Encrypt免费SSL证书：

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期（certbot会自动配置）
```

或者手动配置HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:5002;
        # ... 其他配置同上
    }
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 移动端适配

- 所有页面都已适配移动端
- 支持触摸操作
- 响应式布局，自动适配不同屏幕尺寸
- 地图在移动端显示在底部面板

## 故障排查

### 常见问题

1. **无法登录**
   - 检查 `.env` 文件中的用户名和密码配置
   - 确认密码没有多余的空格

2. **地图无法显示**
   - 检查高德地图API密钥是否正确配置
   - 检查浏览器控制台是否有错误信息
   - 确认API密钥配额是否充足

3. **搜索失败**
   - 检查网络连接
   - 检查API密钥配额
   - 查看服务日志：`sudo journalctl -u cluster-finder -f`

4. **端口被占用**
   - 修改 `.env` 中的 `PORT` 配置
   - 或使用其他端口：`gunicorn --bind 0.0.0.0:8000 app:app`

5. **服务无法启动**
   - 检查Python版本：`python3 --version`（需要3.7+）
   - 检查依赖是否安装：`pip list | grep flask`
   - 检查权限：确保启动脚本有执行权限 `chmod +x start_production.sh`

6. **gunicorn启动失败**
   - 检查gunicorn是否安装：`pip list | grep gunicorn`
   - 检查端口是否被占用：`netstat -tulpn | grep 5002`
   - 查看详细错误：`gunicorn --bind 0.0.0.0:5002 app:app --log-level debug`

### 性能优化

1. **调整工作进程数**
   ```bash
   # 在 gunicorn.conf.py 或命令行中设置
   workers = 4  # 根据CPU核心数调整
   ```

2. **启用预加载应用**
   ```python
   # 在 gunicorn.conf.py 中
   preload_app = True  # 减少内存占用
   ```

3. **设置请求限制**
   ```python
   # 在 gunicorn.conf.py 中
   max_requests = 1000  # 工作进程处理1000个请求后重启
   max_requests_jitter = 50
   ```

### 监控建议

1. **查看服务状态**
   ```bash
   sudo systemctl status cluster-finder
   ```

2. **查看实时日志**
   ```bash
   sudo journalctl -u cluster-finder -f
   ```

3. **查看资源使用**
   ```bash
   # 查看进程
   ps aux | grep gunicorn
   
   # 查看端口占用
   netstat -tulpn | grep 5002
   ```

