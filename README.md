# 商圈查找工具

[English](README_EN.md)

基于高德地图 API 的商圈查找工具 — 找出指定城市中多个品牌门店都在一定距离范围内的聚集区域。

## 功能特点

- 🔍 通过高德地图 API 搜索指定城市内的品牌门店，自动分页和去重
- 📏 使用 Haversine 公式精确计算门店间距离
- 🎯 空间网格索引 + 候选集剪枝的优化聚合算法，大幅减少组合检查量
- ⭐ 支持"必选品牌"功能，部分匹配时优先保证指定品牌
- 🗺️ 高德地图 JS API 2.0 交互式地图可视化（标记、连线、信息窗口）
- 🌐 Web 界面支持 SSE 实时进度推送，移动端响应式适配
- 💻 CLI 命令行工具，支持 JSON / HTML / 日志多种输出格式
- 🖥️ uTools 桌面插件，纯前端实现无需后端

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少配置 AMAP_API_KEY
```

需要在[高德开放平台](https://console.amap.com/)申请以下密钥：

| 配置项 | Key 类型 | 用途 |
|--------|----------|------|
| `AMAP_API_KEY` | Web 服务 | POI 搜索（必需） |
| `AMAP_JS_KEY` | Web 端 (JS API) | 地图显示 |
| `AMAP_SECURITY_CODE` | 安全密钥 | JS API 2.0 必需 |

### 3. 运行

**命令行模式：**

```bash
python main.py --city "深圳" --brands "优衣库,海底捞,星巴克" --threshold 200 --output json,html

# 指定必选品牌
python main.py --city "深圳" --brands "优衣库,海底捞,喜茶" --required-brands "海底捞"
```

**Web 服务模式：**

```bash
# 开发模式
python app.py

# 生产模式
pip install gunicorn
./start_production.sh
```

访问 http://localhost:5002（默认账号：admin / admin123）

## CLI 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--city` | 城市名称（必填） | - |
| `--brands` | 品牌列表，逗号分隔（必填） | - |
| `--threshold` | 距离阈值，浮点数（米） | 200 |
| `--required-brands` | 必选品牌，逗号分隔 | - |
| `--output` | 输出格式：json, html, log | json,log |
| `--json-file` | JSON 输出文件名 | 自动生成 |
| `--html-file` | HTML 输出文件名 | map.html |

## 环境变量

```env
# 高德地图密钥
AMAP_API_KEY=your_web_service_key       # Web 服务 Key（必需）
AMAP_JS_KEY=your_js_api_key             # JS API Key
AMAP_SECURITY_CODE=your_security_code   # JS API 安全密钥

# Web 服务
WEB_USERNAME=admin                       # 登录用户名
WEB_PASSWORD=admin123                    # 登录密码
SECRET_KEY=your-secret-key               # Flask session 密钥
PORT=5002                                # 服务端口

# 算法参数
DEFAULT_DISTANCE_THRESHOLD=200           # 默认距离阈值（米）
DEDUPLICATION_DISTANCE=200               # 门店去重距离（米）

# 运行模式
FLASK_DEBUG=False                        # Flask 调试模式
WORKERS=4                               # gunicorn 工作进程数
```

## 项目结构

```
where_will_we_go/
├── main.py                        # CLI 入口
├── app.py                         # Flask Web 应用
├── config.py                      # 配置加载
├── amap_api.py                    # 高德 API 封装（搜索、去重、限流重试）
├── cluster_finder.py              # 聚类入口（委托优化/暴力版本）
├── cluster_finder_optimized.py    # 优化算法（空间索引 + 候选集剪枝）
├── distance.py                    # Haversine 距离计算
├── output.py                      # 输出模块（JSON / 日志 / HTML 地图）
├── log_capture.py                 # 日志捕获（stdout → SSE 回调）
├── templates/                     # Web 模板
│   ├── login.html                 # 登录页
│   ├── search.html                # 搜索页（含品牌标签、进度条）
│   ├── result.html                # 结果页
│   └── map_view.html              # 地图页
├── utools_plugin/                 # uTools 桌面插件（纯 JS）
├── gunicorn.conf.py               # gunicorn 生产配置
├── start_production.sh            # 生产启动脚本
├── cluster-finder.service.example # systemd 服务模板
├── requirements.txt               # Python 依赖
└── SDD-docs/                      # SDD 规范文档
```

## 核心架构

```
main.py (CLI)  ──┐
                  ├──▶ amap_api.py ──▶ cluster_finder.py ──▶ output.py
app.py  (Flask) ──┘        │                │
                       config.py        distance.py
```

1. **amap_api.py** — 高德 REST API 封装，自动分页、限流重试、门店去重
2. **cluster_finder.py** — 委托优化算法（SpatialGrid 空间索引），回退暴力算法
3. **output.py** — 生成 JSON / 日志 / 自包含 HTML 地图

## 算法原理

1. **POI 搜索** — 对每个品牌，通过高德 API 搜索目标城市中的所有门店
2. **空间索引** — 构建网格空间索引（网格大小 = 2× 距离阈值）
3. **候选集剪枝** — 对每个门店，查找阈值范围内其他品牌的门店
4. **组合检查** — 仅对可行的门店组合使用 Haversine 公式验证距离
5. **部分品牌回退** — 若无全品牌匹配，从多到少枚举品牌子集（≥2 个品牌）
6. **必选品牌过滤** — 回退时跳过不包含所有必选品牌的子集
7. **商圈去重** — 每个门店只归属一个商圈（贪心：优先品牌数多、距离小的）

## 生产部署

```bash
# gunicorn + systemd
sudo cp cluster-finder.service.example /etc/systemd/system/cluster-finder.service
# 编辑配置文件中的路径和用户
sudo systemctl enable cluster-finder
sudo systemctl start cluster-finder
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 地图不显示底图 | 缺少 JS API 安全密钥 | 配置 `AMAP_JS_KEY` + `AMAP_SECURITY_CODE` |
| USERKEY_PLAT_NOMATCH | Key 类型不匹配 | JS API 用 Web 端类型 Key |
| 搜索不到门店 | 品牌名不准确 / 配额用尽 | 使用官方品牌名 |
| API 限流 | 请求过快 | 程序自动重试，或减少品牌数 |

## 技术栈

Python 3.7+ · Flask · 高德地图 JS API 2.0 · gunicorn · 原生 JavaScript

## License

MIT License
