# 模块详细设计

**版本**：v1.0
**最后更新**：2026-03-05

---

## 1. config.py — 配置管理

**职责**：从 `.env` 文件加载配置，提供全局配置常量。

**依赖**：`python-dotenv`

**导出常量**：

| 常量 | 类型 | 默认值 | 来源环境变量 | 说明 |
|------|------|--------|-------------|------|
| `AMAP_API_KEY` | str | `""` | `AMAP_API_KEY` | 高德 REST API 密钥 |
| `AMAP_JS_KEY` | str | 同 API_KEY | `AMAP_JS_KEY` | 高德 JS API 密钥 |
| `AMAP_SECURITY_CODE` | str | `""` | `AMAP_SECURITY_CODE` | JS API 安全密钥 |
| `AMAP_BASE_URL` | str | `https://restapi.amap.com/v3` | - | API 基础 URL |
| `DEFAULT_DISTANCE_THRESHOLD` | int | `200` | `DEFAULT_DISTANCE_THRESHOLD` | 默认距离阈值 |
| `DEDUPLICATION_DISTANCE` | float | `200.0` | `DEDUPLICATION_DISTANCE` | 门店去重距离 |
| `POI_SEARCH_ENDPOINT` | str | `/place/text` | - | POI 搜索路径 |

---

## 2. distance.py — 距离计算

**职责**：提供地理距离计算函数。

**依赖**：标准库 (`math`)

**公开函数**：

### `haversine_distance(lat1, lon1, lat2, lon2) -> float`
计算两点间大圆距离（米）。

### `check_all_distances(stores, threshold) -> Tuple[bool, float]`
检查所有门店两两距离是否 ≤ 阈值。返回 `(是否满足, 最大距离)`。

### `calculate_max_distance(stores) -> float`
计算门店列表中的最大距离。

---

## 3. amap_api.py — 高德 API 封装

**职责**：封装高德地图 POI 搜索，包含分页、限流重试、门店去重。

**依赖**：`requests`, `config.py`, `distance.py`

**常量**：

| 常量 | 值 | 说明 |
|------|-----|------|
| `REQUEST_DELAY` | 0.2s | 请求间隔 |
| `RATE_LIMIT_RETRY_DELAY` | 2.0s | 限流重试基础延迟 |
| `MAX_RETRIES` | 3 | 最大重试次数 |

**公开函数**：

### `deduplicate_stores(stores, distance_threshold=DEDUPLICATION_DISTANCE) -> List[Dict]`
按距离阈值去重门店列表。在距离相近的门店中保留名称最长的。

### `search_poi(city, keyword, max_pages=10) -> List[Dict]`
搜索指定城市中某关键词的 POI。
- 自动分页（每页 20 条，最多 `max_pages` 页）
- 限流重试（`CUQPS_HAS_EXCEEDED_THE_LIMIT` 或 `infocode=10009`）
- 自动调用 `deduplicate_stores()` 去重
- 返回 `List[Store]`

### `search_brands_with_progress(city, brands, progress_callback=None) -> Dict[str, List[Dict]]`
搜索多个品牌。对每个品牌调用 `search_poi()`。
- `progress_callback(brand, current, total, message)` 用于进度通知
- 品牌间有额外延迟 (`REQUEST_DELAY * 2`)

### `search_brands(city, brands) -> Dict[str, List[Dict]]`
`search_brands_with_progress` 的无回调版本。

---

## 4. cluster_finder.py — 聚类入口

**职责**：商圈查找的统一入口，委托优化/暴力版本执行，并对结果去重。

**依赖**：`distance.py`, 可选 `cluster_finder_optimized.py`

**内部函数**：

### `_store_key(store) -> str`
生成门店唯一标识（优先 `poi_id`，回退到坐标字符串）。

### `_deduplicate_clusters(clusters) -> List[Dict]`
商圈去重：按 `brand_count↓ + max_distance↑` 排序，贪心确保每门店只出现一次。

**公开函数**：

### `find_clusters(brand_stores_dict, threshold, required_brands=None, use_optimized=True) -> List[Dict]`
主入口函数。
- `brand_stores_dict`：品牌-门店字典
- `threshold`：距离阈值（米）
- `required_brands`：必选品牌列表
- `use_optimized`：是否使用优化算法
- 返回去重后的商圈列表

**流程**：
1. 若优化版本可用且启用 → 调用 `find_clusters_optimized()`
2. 否则使用暴力 Cartesian product
3. 若全品牌无结果 → 部分品牌回退（`combinations` 枚举）
4. 对结果调用 `_deduplicate_clusters()`

---

## 5. cluster_finder_optimized.py — 优化聚类算法

**职责**：使用空间索引和候选集剪枝的优化聚类算法。

**依赖**：`distance.py`

**类**：

### `SpatialGrid`
空间网格索引。

**方法**：
- `__init__(stores, threshold)` — 构建网格，`grid_size = threshold * 2`
- `_get_grid_key(lat, lon) -> Tuple[int, int]` — 坐标到网格键的映射
- `get_nearby_stores(store_idx) -> Set[int]` — 获取附近门店索引（3×3 邻域 + 精确距离检查）

**公开函数**：

### `find_clusters_optimized(brand_stores_dict, threshold, required_brands=None) -> List[Dict]`
优化版聚类算法。
1. 构建门店索引映射
2. 构建 `SpatialGrid`
3. 为每个品牌的门店构建候选集
4. 使用候选集组合查找全品牌商圈
5. 部分品牌回退（含必选品牌过滤）

---

## 6. output.py — 结果输出

**职责**：将商圈结果输出为 JSON、文本日志或 HTML 地图。

**依赖**：`config.py` (读取 JS API Key 和安全密钥)

**公开函数**：

### `output_json(clusters, filename=None) -> str`
生成 JSON 字符串。若提供 `filename` 则同时写入文件。

### `output_log(clusters)`
命令行格式化输出商圈信息（品牌、门店、距离）。

### `output_html(clusters, city, filename="map.html") -> str`
生成独立 HTML 地图文件。调用 `output_html_string()` 并写入文件。

### `output_html_string(clusters, city) -> str`
生成自包含 HTML 字符串。内容包括：
- 高德 JS API 2.0 加载（含安全密钥配置）
- 地图初始化（中心点为所有门店的平均坐标）
- 每个商圈：彩色标记 + 连接线 + 信息窗口
- 侧边栏：商圈信息面板（可点击跳转）

---

## 7. log_capture.py — 日志捕获

**职责**：将 `print()` 输出重定向到回调函数，用于 SSE 流推送。

**依赖**：标准库

**类**：

### `LogCapture(callback=None)`
上下文管理器，临时替换 `sys.stdout`。

**方法**：
- `write(text)` — 缓冲文本，按换行拆分处理
- `_process_line(line)` — 过滤 tqdm 进度条字符，调用回调
- `flush()` — 刷新当前缓冲行
- `__enter__` / `__exit__` — 替换/恢复 `sys.stdout`

**使用模式**：
```python
def log_callback(message):
    queue.put({'type': 'log', 'message': message})

with LogCapture(log_callback):
    find_clusters(...)  # 内部的 print() 都被捕获
```

---

## 8. app.py — Flask Web 应用

**职责**：提供 Web 界面和 API 端点。

**依赖**：所有核心模块 + Flask + werkzeug

**内部函数**：

### `login_required(f)` — 装饰器
检查 `session['user_id']`，未登录重定向到 `/login`。

### `_validate_search_params(data) -> (city, brands, threshold, required_brands)`
验证搜索参数，校验规则：
- city 非空
- brands 非空
- API Key 已配置
- threshold 为数字且在 50-5000 范围
- required_brands 是 brands 的子集

### `_run_threaded_task(task_fn, msg_queue)` — 生成器
在后台线程执行任务，yield queue 中的 SSE 消息。返回 `(result, error)`。

### `_sse_msg(msg_type, message=None, **extra) -> str`
构造 SSE 消息字符串。

**路由**：

| 方法 | 路径 | 处理函数 | 说明 |
|------|------|----------|------|
| GET | `/` | `index()` | 重定向 |
| GET/POST | `/login` | `login()` | 登录 |
| GET | `/logout` | `logout()` | 登出 |
| GET | `/search` | `search()` | 搜索页 |
| POST | `/api/search/stream` | `api_search_stream()` | SSE 搜索 |
| POST | `/api/search` | `api_search()` | 同步搜索 |
| GET | `/result` | `result()` | 结果页 |
| GET | `/map` | `map_view()` | 地图页 |

---

## 9. main.py — CLI 入口

**职责**：命令行入口，解析参数，调用核心管线。

**依赖**：`amap_api.py`, `cluster_finder.py`, `output.py`, `config.py`

**流程**：
1. `argparse` 解析参数（city, brands, threshold, required-brands, output, json-file, html-file）
2. 校验 API Key
3. 解析品牌列表和必选品牌
4. 校验必选品牌 ⊂ 品牌列表
5. `search_brands()` 搜索门店
6. `find_clusters()` 聚类（传入 required_brands）
7. 根据 output 格式调用对应的 `output_*()` 函数

---

## 10. uTools 插件模块

### utools_plugin/distance.js
Python `distance.py` 的 JS 实现。函数：`haversineDistance()`, `checkAllDistances()`。

### utools_plugin/amap_api.js
Python `amap_api.py` 的 JS 实现。函数：`searchPOI()`, `searchBrands()`。
- 直接从浏览器调用高德 REST API
- 无门店去重逻辑

### utools_plugin/cluster_finder.js
Python 优化算法的 JS 实现。类：`SpatialGrid`。函数：`findClusters()`。
- 包含部分品牌回退
- 无必选品牌功能

### utools_plugin/output.js
Python `output.py` 的 JS 实现。函数：`generateMapHTML()`, `openMapInNewWindow()`, `downloadHTML()`。

### utools_plugin/preload.js
uTools 生命周期回调：`onPluginReady`, `onPluginEnter`, `onPluginOut`。
暴露 `saveAndOpenHTML()` 文件操作函数。

### utools_plugin/index.html
插件主界面。功能：搜索表单、API Key 配置面板、结果展示。

### utools_plugin/server.py
可选的 Flask 后端（端口 8765），提供 `/api/find_clusters` 和 `/api/open_html`。
