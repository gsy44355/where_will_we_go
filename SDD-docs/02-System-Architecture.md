# 系统架构设计文档

**版本**：v1.0
**最后更新**：2026-03-05

---

## 1. 架构概览

系统采用共享核心管线 + 多入口架构。CLI 和 Web 两个入口共用同一套搜索、聚类、输出管线，uTools 插件为独立的纯 JS 前端实现。

```
┌─────────────────────────────────────────────────────────┐
│                      用户入口层                          │
├──────────┬──────────────────┬────────────────────────────┤
│ main.py  │   app.py         │  utools_plugin/            │
│ (CLI)    │   (Flask Web)    │  (纯 JS 桌面插件)           │
│ argparse │   SSE Stream     │  index.html + JS modules   │
└────┬─────┴────────┬─────────┴────────────────────────────┘
     │              │
     ▼              ▼
┌────────────────────────────────────────┐
│           核心管线 (Python)             │
├────────────────────────────────────────┤
│  amap_api.py        POI 搜索 + 去重    │
│       │                                │
│       ▼                                │
│  cluster_finder.py  聚类入口           │
│       │                                │
│       ├──▶ cluster_finder_optimized.py │
│       │    (空间索引优化算法)           │
│       │                                │
│       ├──▶ distance.py                 │
│       │    (Haversine 距离计算)         │
│       │                                │
│       ▼                                │
│  output.py          结果输出            │
│  (JSON / Log / HTML)                   │
├────────────────────────────────────────┤
│  config.py          配置加载 (.env)     │
│  log_capture.py     日志捕获 (SSE用)    │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│         外部服务                        │
├────────────────────────────────────────┤
│  高德地图 REST API  (/v3/place/text)   │
│  高德地图 JS API 2.0 (地图渲染)         │
└────────────────────────────────────────┘
```

---

## 2. 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端语言 | Python 3.7+ | 核心逻辑 |
| Web 框架 | Flask 3.0+ | HTTP 服务 |
| 模板引擎 | Jinja2 (Flask 内置) | HTML 页面渲染 |
| WSGI 服务器 | gunicorn (生产) | 多进程部署 |
| HTTP 客户端 | requests | 调用高德 API |
| 配置管理 | python-dotenv | 加载 .env |
| 进度显示 | tqdm | CLI 进度条 |
| 前端地图 | 高德地图 JS API 2.0 | 地图标注与交互 |
| 前端样式 | 纯 CSS (无框架) | UI 样式 |
| 前端交互 | 原生 JavaScript | 无框架依赖 |
| 桌面插件 | uTools + 原生 JS | 桌面端入口 |

---

## 3. 模块依赖关系

```
config.py ◀──── amap_api.py ◀──── main.py
    ▲               │                  │
    │               ▼                  ▼
    ├───── output.py ◀──── cluster_finder.py ◀──── app.py
    │                           │                    │
    │                           ▼                    │
    │              cluster_finder_optimized.py        │
    │                           │                    │
    │                           ▼                    │
    └───── distance.py ◀────────┘                    │
                                                     │
                                        log_capture.py
```

**依赖方向说明**：
- `config.py`：被所有需要配置的模块引用（零依赖）
- `distance.py`：被 `amap_api.py` 和 `cluster_finder*.py` 引用
- `amap_api.py`：依赖 `config.py` 和 `distance.py`
- `cluster_finder.py`：依赖 `distance.py`，可选依赖 `cluster_finder_optimized.py`
- `output.py`：依赖 `config.py`（读取 JS API Key）
- `app.py`：依赖除 `main.py` 外的所有模块
- `main.py`：依赖 `amap_api.py`、`cluster_finder.py`、`output.py`、`config.py`
- `log_capture.py`：零依赖（仅使用标准库）

---

## 4. 数据流

### 4.1 CLI 数据流

```
用户输入 (argparse)
  │
  ├─ city, brands[], threshold, required_brands[]
  │
  ▼
amap_api.search_brands(city, brands)
  │
  ├─ 对每个品牌调用 search_poi() → 高德 REST API
  ├─ 自动分页 (每页20条, 最多10页)
  ├─ 限流重试 (最多3次, 递增延迟)
  ├─ deduplicate_stores() 门店去重
  │
  ▼
Dict[brand, List[Store]]
  │
  ▼
cluster_finder.find_clusters(brand_stores, threshold, required_brands)
  │
  ├─ 优先 → find_clusters_optimized()
  │   ├─ SpatialGrid 空间索引
  │   ├─ 候选集构建与剪枝
  │   └─ 部分品牌回退 (含必选品牌过滤)
  ├─ 回退 → 暴力 Cartesian product
  ├─ _deduplicate_clusters() 商圈去重
  │
  ▼
List[Cluster]
  │
  ├─ output_json()  → JSON 文件
  ├─ output_log()   → 控制台输出
  └─ output_html()  → HTML 地图文件
```

### 4.2 Web SSE 数据流

```
浏览器 POST /api/search/stream
  │  { city, brands, threshold, required_brands }
  │
  ▼
Flask generate() 生成器
  │
  ├─ _validate_search_params() → 参数校验
  │
  ├─ 搜索阶段 (后台线程)
  │   ├─ LogCapture 捕获 print() → SSE log 消息
  │   ├─ progress_callback → SSE progress 消息
  │   └─ search_brands_with_progress()
  │
  ├─ 聚类阶段 (后台线程)
  │   ├─ LogCapture 捕获 print() → SSE log 消息
  │   └─ find_clusters()
  │
  └─ 结果阶段
      ├─ output_html_string() → HTML 地图内容
      └─ SSE complete 消息 (含 result + html_content)
          │
          ▼
      浏览器接收 SSE
          ├─ 更新进度条
          ├─ 追加日志
          └─ 切换到结果视图 (地图 + 侧边栏)
```

---

## 5. 部署架构

### 5.1 开发环境

```
┌──────────────────────┐
│ python app.py        │
│ Flask dev server     │
│ port: 5002           │
│ single process       │
└──────────────────────┘
```

### 5.2 生产环境

```
┌──────────────────────────────────────────┐
│            systemd 服务管理               │
│  cluster-finder.service                  │
├──────────────────────────────────────────┤
│           gunicorn WSGI 服务器            │
│  bind: 0.0.0.0:5002                     │
│  workers: CPU*2+1 (sync)                │
│  timeout: 120s                          │
│  preload_app: True                      │
│  max_requests: 1000 (+ jitter 50)       │
├──────────────────────────────────────────┤
│           Flask 应用 (app.py)            │
│  session-based auth                     │
│  SSE streaming endpoints               │
│  background threads for search/cluster  │
└──────────────────────────────────────────┘
         │
         ▼
  高德地图 REST API (HTTPS)
```

---

## 6. SSE 流式通信架构

Web 搜索使用 Server-Sent Events 实现实时进度推送。

```
浏览器                         Flask
  │                              │
  │  POST /api/search/stream     │
  │  ─────────────────────────▶  │
  │                              │
  │  Content-Type: text/event-stream
  │  ◀─────────────────────────  │
  │                              │
  │  data: {"type":"progress",   │
  │         "stage":"searching", │  ← 后台线程通过 queue 发送
  │         "progress":10,...}   │
  │  ◀─────────────────────────  │
  │                              │
  │  data: {"type":"log",        │
  │         "message":"..."}     │  ← LogCapture 重定向 print()
  │  ◀─────────────────────────  │
  │                              │
  │  data: {"type":"complete",   │
  │         "result":{...},      │
  │         "html_content":"..."│  ← 搜索完成
  │         }                    │
  │  ◀─────────────────────────  │
  │                              │
  │  连接关闭                     │
```

**线程模型**：
- 主线程：Flask 请求处理 + generate() 生成器
- 后台线程：执行搜索/聚类任务
- 通信方式：`queue.Queue` 传递 SSE 消息
- `_run_threaded_task()`：封装线程创建、queue 消费、错误传播

---

## 7. uTools 插件架构

uTools 插件是一个独立的纯前端 JavaScript 实现，不依赖 Python 后端。

```
┌─────────────────────────────────────────┐
│              uTools 桌面应用             │
├─────────────────────────────────────────┤
│  plugin.json         插件配置            │
│  preload.js          预加载脚本          │
│  index.html          主界面              │
│  ├── distance.js     距离计算            │
│  ├── amap_api.js     高德 API 调用       │
│  ├── cluster_finder.js  聚类算法         │
│  └── output.js       HTML 地图生成       │
├─────────────────────────────────────────┤
│  server.py (可选)     Flask 后端         │
│  port: 8765          仅开发/调试用       │
└─────────────────────────────────────────┘
         │
         ▼
  高德地图 REST API (直接从浏览器调用)
```

**与 Python 版本的关系**：
- `distance.js` ≈ `distance.py`（Haversine 公式的 JS 实现）
- `amap_api.js` ≈ `amap_api.py`（高德 API 调用的 JS 实现，无去重）
- `cluster_finder.js` ≈ `cluster_finder_optimized.py`（空间索引优化算法的 JS 实现）
- `output.js` ≈ `output.py`（HTML 地图生成的 JS 实现）
- API Key 存储在 `utools.dbStorage` 或 `localStorage`

---

## 8. 关键架构决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 算法分离 | `cluster_finder.py` + `cluster_finder_optimized.py` | 优化版本可选加载，降级回退 |
| SSE vs WebSocket | SSE | 单向推送足够，实现更简单 |
| 线程 vs 异步 | threading | Flask sync worker 兼容性好 |
| 日志传递 | stdout 重定向 (LogCapture) | 无侵入改造已有 print() 代码 |
| HTML 地图 | 自包含 HTML 字符串 | 无需额外静态文件，可独立打开 |
| 前端框架 | 无（原生 JS） | 项目规模小，减少依赖 |
| 认证方式 | session-based (werkzeug) | 简单场景足够 |
