# 配置与环境规范

**版本**：v1.0
**最后更新**：2026-03-05

---

## 1. 环境变量配置 (.env)

所有配置通过项目根目录的 `.env` 文件管理，由 `python-dotenv` 加载。

### 1.1 配置项清单

| 变量名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `AMAP_API_KEY` | string | 是 | `""` | 高德地图 Web 服务类型 API Key，用于 REST API POI 搜索 |
| `AMAP_JS_KEY` | string | 否 | 同 `AMAP_API_KEY` | 高德地图 JS API Key，用于 Web 端地图显示 |
| `AMAP_SECURITY_CODE` | string | 是* | `""` | 高德 JS API 2.0 安全密钥（*Web 地图显示必需） |
| `WEB_USERNAME` | string | 否 | `admin` | Web 登录用户名 |
| `WEB_PASSWORD` | string | 否 | `admin123` | Web 登录密码 |
| `SECRET_KEY` | string | 否 | `your-secret-key-change-this-in-production` | Flask session 加密密钥 |
| `DEFAULT_DISTANCE_THRESHOLD` | int | 否 | `200` | 默认距离阈值（米） |
| `DEDUPLICATION_DISTANCE` | float | 否 | `200` | 门店去重距离阈值（米） |
| `PORT` | int | 否 | `5002` | Web 服务端口 |
| `FLASK_DEBUG` | string | 否 | `False` | Flask 调试模式（`true`/`false`） |
| `WORKERS` | int | 否 | `4` | gunicorn 工作进程数 |

### 1.2 .env 文件示例

```env
# 高德地图 API 密钥
AMAP_API_KEY=your_web_service_api_key
AMAP_JS_KEY=your_js_api_key
AMAP_SECURITY_CODE=your_security_code

# Web 登录凭据
WEB_USERNAME=admin
WEB_PASSWORD=your_secure_password

# Flask 配置
SECRET_KEY=your-random-secret-key
PORT=5002
FLASK_DEBUG=False

# 算法参数
DEFAULT_DISTANCE_THRESHOLD=200
DEDUPLICATION_DISTANCE=200

# 生产环境
WORKERS=4
```

---

## 2. 高德开放平台 Key 申请

### 2.1 需要的 Key 类型

本项目需要两种类型的高德 Key：

| Key 类型 | 平台类型 | 用途 | 配置变量 |
|----------|----------|------|----------|
| Web 服务 | 服务端 | POI 搜索 REST API | `AMAP_API_KEY` |
| Web 端 (JS API) | 浏览器 | 地图显示 | `AMAP_JS_KEY` + `AMAP_SECURITY_CODE` |

### 2.2 申请步骤

1. 注册高德开放平台账号：https://lbs.amap.com/
2. 创建应用
3. 添加 Key：
   - 选择"Web 服务"类型 → 获得 REST API Key (`AMAP_API_KEY`)
   - 选择"Web 端 (JS API)"类型 → 获得 JS Key (`AMAP_JS_KEY`) + 安全密钥 (`AMAP_SECURITY_CODE`)

### 2.3 安全密钥说明

高德 JS API 2.0 要求配置安全密钥，否则地图无法加载。安全密钥通过全局变量注入：

```javascript
window._AMapSecurityConfig = {
    securityJsCode: 'your_security_code'
};
```

若未配置 `AMAP_SECURITY_CODE`，Web 端地图功能将不可用，但 REST API 搜索功能正常。

---

## 3. Python 依赖

### 3.1 requirements.txt

```
requests>=2.31.0      # HTTP 客户端（高德 API 调用）
tqdm>=4.66.0          # CLI 进度条
flask>=3.0.0          # Web 框架
werkzeug>=3.0.0       # WSGI 工具库（密码哈希、安全）
python-dotenv>=1.0.0  # 环境变量加载

# 生产环境推荐安装（可选）
# gunicorn>=21.2.0
```

### 3.2 uTools 插件额外依赖

```
flask-cors>=4.0.0     # 仅 utools_plugin/server.py 需要
```

---

## 4. 运行环境要求

| 项目 | 要求 |
|------|------|
| Python 版本 | 3.7+ |
| 操作系统 | Linux / macOS / Windows |
| 网络 | 需要访问高德 API (`restapi.amap.com`, `webapi.amap.com`) |
| 磁盘 | 结果目录 `results/`（自动创建） |

---

## 5. 配置加载顺序

```python
# config.py 加载逻辑
from dotenv import load_dotenv
load_dotenv()  # 1. 加载 .env 文件到环境变量

AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")            # 2. 读取环境变量
AMAP_JS_KEY = os.getenv("AMAP_JS_KEY", "") or AMAP_API_KEY  # 3. JS Key 回退到 API Key
```

**优先级**：系统环境变量 > `.env` 文件 > 代码默认值

---

## 6. 安全注意事项

| 项目 | 默认值 | 生产环境建议 |
|------|--------|-------------|
| `SECRET_KEY` | 硬编码字符串 | 使用随机生成的长密钥 |
| `WEB_USERNAME` | `admin` | 更换为非默认用户名 |
| `WEB_PASSWORD` | `admin123` | 更换为强密码 |
| `FLASK_DEBUG` | `False` | 确保为 `False` |
| API Key | 无 | 不要提交到版本控制 |

`.env` 文件应加入 `.gitignore`，避免密钥泄露。
