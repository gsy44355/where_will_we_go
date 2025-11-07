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

### 开发模式
```bash
python app.py
```

### 生产模式（使用gunicorn）
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 使用systemd服务（推荐）

创建 `/etc/systemd/system/cluster-finder.service`：
```ini
[Unit]
Description=商圈查找Web服务
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/where_will_we_go
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable cluster-finder
sudo systemctl start cluster-finder
```

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

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 移动端适配

- 所有页面都已适配移动端
- 支持触摸操作
- 响应式布局，自动适配不同屏幕尺寸
- 地图在移动端显示在底部面板

## 故障排查

1. **无法登录**：检查 `.env` 文件中的用户名和密码配置
2. **地图无法显示**：检查高德地图API密钥是否正确配置
3. **搜索失败**：检查网络连接和API密钥配额
4. **端口被占用**：修改 `.env` 中的 `PORT` 配置

