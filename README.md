# 商圈查找工具

基于高德地图API的商圈查找工具，可以找出指定城市中多个品牌门店都在一定距离范围内的商圈。

## 功能特点

- 🔍 通过高德地图API搜索指定城市内的品牌门店
- 📏 使用Haversine公式计算门店间距离
- 🎯 找出所有品牌门店都在指定距离内的商圈
- 🗺️ 支持高德地图可视化展示
- 🌐 提供Web界面，支持移动端访问
- 📊 支持JSON、HTML地图和命令行日志多种输出方式

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件，填写高德地图API密钥
nano .env  # 或使用其他编辑器
```

### 3. 获取高德地图API密钥

访问 [高德开放平台](https://console.amap.com/) 创建应用并获取以下密钥：

| 配置项 | 类型 | 用途 |
|--------|------|------|
| `AMAP_API_KEY` | Web服务 | 后端POI搜索 |
| `AMAP_JS_KEY` | Web端(JS API) | 前端地图显示 |
| `AMAP_SECURITY_CODE` | 安全密钥 | JS API 2.0必需 |

> ⚠️ **注意**：高德地图JS API 2.0 要求配置安全密钥，否则地图底图无法显示。

### 4. 运行

#### 方式一：命令行模式

```bash
python main.py --city "北京" --brands "优衣库,丰茂烤肉" --output json,html
```

#### 方式二：Web服务模式

```bash
# 开发模式
python app.py

# 生产模式（推荐）
pip install gunicorn
./start_production.sh
```

访问 http://localhost:5002 使用Web界面（默认账号：admin/admin123）

## 命令行使用

```bash
python main.py --city "城市" --brands "品牌1,品牌2" [选项]
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--city` | 城市名称（必填） | - |
| `--brands` | 品牌列表，逗号分隔（必填） | - |
| `--threshold` | 距离阈值（米） | 200 |
| `--output` | 输出格式：json, html, log | json,log |
| `--json-file` | JSON输出文件名 | 自动生成 |
| `--html-file` | HTML输出文件名 | map.html |

### 示例

```bash
# 查找北京地区优衣库和丰茂烤肉的商圈
python main.py --city "北京" --brands "优衣库,丰茂烤肉"

# 指定300米距离阈值，并生成HTML地图
python main.py --city "上海" --brands "星巴克,麦当劳" --threshold 300 --output json,html

# 多个品牌，自定义输出文件
python main.py --city "深圳" --brands "优衣库,海底捞,喜茶" --html-file result.html
```

## 配置说明

在 `.env` 文件中配置以下环境变量：

```env
# === 必需配置 ===
# Web服务 API Key（用于POI搜索）
AMAP_API_KEY=your_web_service_api_key

# Web端(JS API) Key（用于地图显示）
AMAP_JS_KEY=your_js_api_key

# JS API 安全密钥（地图显示必需）
AMAP_SECURITY_CODE=your_security_code

# === 可选配置 ===
# Web服务
SECRET_KEY=your-secret-key          # Session密钥
WEB_USERNAME=admin                   # 登录用户名
WEB_PASSWORD=admin123                # 登录密码
PORT=5002                            # 服务端口

# 搜索参数
DEFAULT_DISTANCE_THRESHOLD=200       # 默认距离阈值（米）
DEDUPLICATION_DISTANCE=200           # 门店去重距离（米）
```

## 输出说明

- **JSON输出**：结构化的商圈数据，包含门店名称、地址、坐标等
- **HTML输出**：交互式高德地图，标注所有商圈和门店
- **日志输出**：命令行详细显示查找过程和结果

## 项目结构

```
where_will_we_go/
├── app.py                    # Flask Web应用主文件
├── main.py                   # 命令行主程序
├── config.py                 # 配置文件
├── amap_api.py              # 高德地图API封装
├── distance.py              # 距离计算模块
├── cluster_finder.py        # 商圈查找算法
├── cluster_finder_optimized.py  # 优化版商圈查找
├── output.py                # 结果输出模块
├── log_capture.py           # 日志捕获工具
├── gunicorn.conf.py         # Gunicorn配置
├── requirements.txt         # Python依赖
├── .env.example             # 环境变量模板
├── templates/               # Web模板
│   ├── login.html          # 登录页
│   ├── search.html         # 搜索页
│   ├── result.html         # 结果页
│   └── map_view.html       # 地图页
├── start_web.sh            # 开发环境启动脚本
├── start_production.sh     # 生产环境启动脚本
├── cluster-finder.service.example  # Systemd服务配置模板
├── README.md               # 本文档
├── WEB_DEPLOY.md           # Web部署详细文档
└── PRODUCTION.md           # 生产环境快速指南
```

## Web服务部署

### 开发模式

```bash
python app.py
# 或
./start_web.sh
```

### 生产模式

推荐使用 gunicorn + systemd 部署：

```bash
# 1. 安装gunicorn
pip install gunicorn

# 2. 使用启动脚本
./start_production.sh

# 3. 或配置为系统服务
sudo cp cluster-finder.service.example /etc/systemd/system/cluster-finder.service
# 编辑配置文件，修改路径
sudo systemctl enable cluster-finder
sudo systemctl start cluster-finder
```

详细部署说明请参考：
- [WEB_DEPLOY.md](WEB_DEPLOY.md) - 完整Web部署文档
- [PRODUCTION.md](PRODUCTION.md) - 生产环境快速指南

## 常见问题

### 1. 地图只显示点，不显示底图

**原因**：高德地图JS API 2.0 需要配置安全密钥

**解决**：
1. 登录 [高德开放平台控制台](https://console.amap.com/)
2. 创建一个 **Web端(JS API)** 类型的Key
3. 获取该Key对应的安全密钥
4. 在 `.env` 中配置 `AMAP_JS_KEY` 和 `AMAP_SECURITY_CODE`

### 2. 报错 USERKEY_PLAT_NOMATCH

**原因**：API Key平台类型不匹配

**解决**：确保 `AMAP_JS_KEY` 是 **Web端(JS API)** 类型的Key，而不是 **Web服务** 类型

### 3. 搜索不到门店

**可能原因**：
- 品牌名称不准确（尝试使用官方名称）
- 城市名称错误
- API配额用尽

### 4. API限流

程序已内置限流处理机制，会自动重试。如果频繁触发限流，可以：
- 减少同时搜索的品牌数量
- 在 `.env` 中调整延迟参数

## 技术栈

- **后端**：Python 3.7+, Flask
- **地图**：高德地图 JS API 2.0
- **部署**：Gunicorn, Systemd, Nginx（可选）

## License

MIT License
