# 数据模型定义

**版本**：v1.0
**最后更新**：2026-03-05

---

## 1. 核心数据结构

### 1.1 Store（门店）

```python
Store = {
    "name": str,        # 门店名称（例："优衣库(万象城店)"）
    "address": str,     # 门店地址（例："福田区深南大道1881号"）
    "lat": float,       # 纬度（例：22.541234）
    "lon": float,       # 经度（例：114.054321）
    "poi_id": str,      # 高德 POI 唯一标识
    "type": str         # POI 类型（例："购物服务;服装鞋帽皮具店"）
}
```

**坐标约定**：
- 高德 API 返回 `location` 字段格式为 `"经度,纬度"`（即 `"lon,lat"`）
- 内部存储使用 `lat`（纬度）和 `lon`（经度）两个独立字段
- 转换代码：`lat = float(location[1])`, `lon = float(location[0])`

### 1.2 Cluster（商圈）

```python
Cluster = {
    "brands": Dict[str, Store],  # 品牌名 → 该品牌在此商圈中的门店
    "stores": List[Store],       # 所有门店列表（顺序与 brands 一致）
    "max_distance": float,       # 商圈内门店两两最大距离（米）
    "brand_count": int           # 包含的品牌数量
}
```

**示例**：
```json
{
    "brands": {
        "优衣库": {"name": "优衣库(万象城店)", "address": "...", "lat": 22.541, "lon": 114.054, "poi_id": "B001", "type": "..."},
        "海底捞": {"name": "海底捞火锅(万象城店)", "address": "...", "lat": 22.542, "lon": 114.055, "poi_id": "B002", "type": "..."}
    },
    "stores": [
        {"name": "优衣库(万象城店)", ...},
        {"name": "海底捞火锅(万象城店)", ...}
    ],
    "max_distance": 156.78,
    "brand_count": 2
}
```

**约束**：
- 每个品牌在一个商圈中只有一个门店
- `brands` 的 key 数量 = `brand_count`
- `stores` 的长度 = `brand_count`
- 所有门店两两距离 ≤ 距离阈值

---

## 2. API 响应数据结构

### 2.1 SearchResult（搜索结果 — 同步 API 返回）

```python
SearchResult = {
    "success": bool,            # 是否成功
    "city": str,                # 搜索城市
    "brands": List[str],        # 找到门店的品牌列表
    "threshold": float,         # 使用的距离阈值
    "cluster_count": int,       # 商圈数量
    "clusters": List[Cluster],  # 商圈列表
    "timestamp": str            # ISO 格式时间戳
}
```

### 2.2 SessionResult（session 中存储的简要结果）

```python
SessionResult = {
    "city": str,
    "brands": List[str],
    "cluster_count": int,
    "timestamp": str
}
```

---

## 3. SSE 消息格式

所有 SSE 消息通过 `data: {JSON}\n\n` 格式传输。

### 3.1 progress（进度消息）

```json
{
    "type": "progress",
    "message": "正在搜索 优衣库...",
    "stage": "searching | clustering | generating",
    "progress": 0-100,
    "brand": "优衣库",          // 可选，搜索阶段
    "current": 1,              // 可选，当前品牌序号
    "total": 3                 // 可选，总品牌数
}
```

### 3.2 log（日志消息）

```json
{
    "type": "log",
    "message": "找到 优衣库 在 深圳 的 42 个门店",
    "stage": "searching | clustering"
}
```

### 3.3 complete（完成消息）

```json
{
    "type": "complete",
    "result": SearchResult,
    "html_content": "<html>...</html>",
    "progress": 100
}
```

### 3.4 error（错误消息）

```json
{
    "type": "error",
    "message": "未找到任何品牌的门店"
}
```

---

## 4. 高德 API 数据映射

### 4.1 POI 搜索请求

```
GET https://restapi.amap.com/v3/place/text
参数:
  key       = AMAP_API_KEY
  keywords  = 品牌名
  city      = 城市名
  offset    = 20 (每页条数)
  page      = 1-10
  extensions = all
```

### 4.2 POI 搜索响应 → Store 映射

```
高德 POI 响应                    内部 Store
─────────────────────────────────────────────
poi.name          →  store.name
poi.address       →  store.address
poi.location      →  "lon,lat" 拆分:
                       store.lon = location[0]
                       store.lat = location[1]
poi.id            →  store.poi_id
poi.type          →  store.type
─────────────────────────────────────────────
response.status   →  "1" 成功 / 其他失败
response.count    →  总结果数（用于分页判断）
response.pois     →  POI 列表
```

---

## 5. HTML 地图数据结构

`output.py` 生成自包含 HTML 时，使用以下 JavaScript 数据结构：

### 5.1 MarkerData（嵌入 HTML 的标记数据）

```javascript
MarkerData = {
    cluster_id: Number,          // 商圈编号（从1开始）
    max_distance: Number,        // 最大距离
    brand_count: Number,         // 品牌数
    markers: [
        {
            name: String,        // 门店名
            address: String,     // 地址
            lat: Number,         // 纬度
            lon: Number,         // 经度
            brand: String        // 品牌名
        }
    ]
}
```

---

## 6. localStorage 键

| 键名 | 类型 | 说明 |
|------|------|------|
| `search_city` | string | 上次搜索城市 |
| `search_brands` | string | 上次搜索品牌（逗号分隔） |
| `search_threshold` | string | 上次距离阈值 |
| `search_required_brands` | JSON array string | 必选品牌列表 |

### sessionStorage 键

| 键名 | 类型 | 说明 |
|------|------|------|
| `searchResult` | JSON string | 完整搜索结果 |
| `htmlContent` | string | HTML 地图内容 |
| `searchElapsed` | string | 搜索耗时（秒） |

---

## 7. 门店唯一标识

用于商圈去重时识别同一门店：

```python
def _store_key(store: Dict) -> str:
    pid = store.get('poi_id')
    if pid:
        return pid  # 优先使用 POI ID
    return f"{store['lat']:.6f},{store['lon']:.6f}"  # 回退到坐标
```
