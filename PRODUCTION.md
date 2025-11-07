# 生产环境快速启动指南

## ⚠️ 重要：生产环境不要使用 `python app.py`

Flask的开发服务器不适合生产环境，应该使用专业的WSGI服务器。

## 快速启动（3种方式）

### 方式1: 使用生产启动脚本（最简单）

```bash
# 1. 安装gunicorn
pip install gunicorn

# 2. 启动服务
./start_production.sh
```

### 方式2: 使用gunicorn命令行

```bash
# 安装gunicorn
pip install gunicorn

# 启动服务
gunicorn --bind 0.0.0.0:5002 --workers 4 --timeout 120 app:app
```

### 方式3: 使用systemd服务（推荐，适合服务器）

```bash
# 1. 安装gunicorn
pip install gunicorn

# 2. 复制并编辑服务文件
sudo cp cluster-finder.service.example /etc/systemd/system/cluster-finder.service
sudo nano /etc/systemd/system/cluster-finder.service
# 修改其中的路径和用户

# 3. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable cluster-finder
sudo systemctl start cluster-finder

# 4. 查看状态
sudo systemctl status cluster-finder
```

## 配置说明

### 环境变量（.env文件）

```env
# 必需配置
AMAP_API_KEY=your_api_key

# 生产环境必需修改
SECRET_KEY=your-secret-key-change-this
WEB_PASSWORD=your-strong-password

# 可选配置
PORT=5002
WORKERS=4
FLASK_DEBUG=False
```

### 工作进程数建议

```bash
# 查看CPU核心数
nproc

# 建议设置为：CPU核心数 * 2 + 1
# 例如：4核CPU → workers = 9
```

## 常用命令

```bash
# 查看服务状态（systemd）
sudo systemctl status cluster-finder

# 查看日志（systemd）
sudo journalctl -u cluster-finder -f

# 重启服务（systemd）
sudo systemctl restart cluster-finder

# 停止服务（systemd）
sudo systemctl stop cluster-finder

# 查看进程（直接启动）
ps aux | grep gunicorn

# 查看端口占用
netstat -tulpn | grep 5002
```

## 完整文档

详细配置和故障排查请参考：`WEB_DEPLOY.md`

