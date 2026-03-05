# API 接口规范

**版本**：v1.0
**最后更新**：2026-03-05

---

## 1. Web 应用 API

基础地址：`http://localhost:5002`

所有 API 端点（除 `/login`）均需要 session 认证。未登录请求将被重定向到 `/login`。

---

### 1.1 POST /login — 用户登录

**请求**：`Content-Type: application/x-www-form-urlencoded`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**成功响应**：`200 OK`
```json
{
    "success": true,
    "redirect": "/search"
}
```

**失败响应**：`401 Unauthorized`
```json
{
    "success": false,
    "message": "用户名或密码错误"
}
```

**副作用**：设置 `session['user_id']` 和 `session['login_time']`

---

### 1.2 GET /logout — 用户登出

**响应**：`302 Redirect → /login`

**副作用**：清除 session

---

### 1.3 GET /search — 搜索页面

**前置条件**：已登录

**响应**：`200 OK`，返回搜索页 HTML

**模板变量**：
- `amap_js_key`：高德 JS API Key
- `amap_security_code`：高德安全密钥

---

### 1.4 POST /api/search/stream — SSE 流式搜索

**前置条件**：已登录

**请求**：`Content-Type: application/json`

```json
{
    "city": "深圳",
    "brands": "优衣库, 海底捞, 星巴克",
    "threshold": 200,
    "required_brands": "海底捞"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| city | string | 是 | 城市名称 |
| brands | string | 是 | 品牌列表（逗号分隔） |
| threshold | number | 否 | 距离阈值（米），默认 200，范围 50-5000 |
| required_brands | string | 否 | 必选品牌列表（逗号分隔） |

**响应**：`Content-Type: text/event-stream`

SSE 消息流（详见 03-Data-Models.md 第 3 节）：

```
data: {"type":"progress","message":"开始搜索 3 个品牌的门店...","stage":"searching","progress":0}

data: {"type":"progress","stage":"searching","brand":"优衣库","current":1,"total":3,"message":"正在搜索 优衣库...","progress":13}

data: {"type":"log","message":"找到 优衣库 在 深圳 的 42 个门店","stage":"searching"}

data: {"type":"progress","message":"正在查找符合条件的商圈...","stage":"clustering","progress":40}

data: {"type":"log","message":"  构建空间索引...","stage":"clustering"}

data: {"type":"complete","result":{...},"html_content":"<!DOCTYPE html>...","progress":100}
```

**错误消息**：
```
data: {"type":"error","message":"请输入城市名称"}
```

**参数校验错误**：
- 城市为空
- 品牌为空
- API Key 未配置
- 阈值不是数字
- 阈值不在 50-5000 范围内
- 必选品牌不是搜索品牌的子集

---

### 1.5 POST /api/search — 同步搜索

**前置条件**：已登录

**请求**：同 1.4

**成功响应**：`200 OK`
```json
{
    "success": true,
    "result": {
        "success": true,
        "city": "深圳",
        "brands": ["优衣库", "海底捞"],
        "threshold": 200,
        "cluster_count": 5,
        "clusters": [...],
        "timestamp": "2026-03-05T10:30:00"
    },
    "html_content": "<!DOCTYPE html>..."
}
```

**失败响应**：

`400 Bad Request`（参数错误）：
```json
{
    "success": false,
    "message": "请输入城市名称"
}
```

`404 Not Found`（无结果）：
```json
{
    "success": false,
    "message": "未找到任何品牌的门店"
}
```

`500 Internal Server Error`：
```json
{
    "success": false,
    "message": "服务器错误: ..."
}
```

---

### 1.6 GET /result — 结果页面

**前置条件**：已登录

**说明**：结果数据从 `sessionStorage` 读取（前端渲染）

---

### 1.7 GET /map — 地图页面

**前置条件**：已登录

**查询参数**（可选）：
| 参数 | 类型 | 说明 |
|------|------|------|
| html | string | URL 编码的 HTML 地图内容 |

**说明**：优先从 URL 参数读取 HTML，否则从 `sessionStorage` 读取

---

## 2. 高德地图 REST API 调用规范

### 2.1 POI 搜索

**端点**：`GET https://restapi.amap.com/v3/place/text`

**请求参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| key | string | Web 服务类型 API Key |
| keywords | string | 搜索关键词（品牌名） |
| city | string | 城市名称 |
| offset | int | 每页结果数，固定 20 |
| page | int | 页码，从 1 开始 |
| extensions | string | 固定 "all" |

**响应处理**：

| 字段 | 处理逻辑 |
|------|----------|
| `status` | `"1"` 成功，其他失败 |
| `info` / `infocode` | 错误信息，`10009` = 限流 |
| `count` | 总结果数 |
| `pois[]` | POI 数组 |
| `pois[].location` | `"经度,纬度"` → 拆分为 `lon, lat` |

**限流处理**：
- 每次请求间隔 0.2 秒 (`REQUEST_DELAY`)
- 品牌间间隔 0.4 秒 (`REQUEST_DELAY * 2`)
- 限流重试延迟：2.0 × (重试次数) 秒
- 最大重试次数：3

**分页逻辑**：
- 每页 20 条，最多 10 页 = 最多 200 条
- 当 `len(stores) >= count` 或 `len(pois) < 20` 时停止

---

## 3. uTools 插件 API（可选后端）

基础地址：`http://localhost:8765`

### 3.1 POST /api/find_clusters — 查找商圈

**请求**：
```json
{
    "city": "深圳",
    "brands": ["优衣库", "海底捞"],
    "threshold": 200,
    "api_key": "your_amap_api_key"
}
```

**响应**：
```json
{
    "clusters": [...],
    "html_file": "/tmp/xxx.html",
    "cluster_count": 5
}
```

### 3.2 POST /api/open_html — 打开 HTML 文件

**请求**：
```json
{
    "html_file": "/tmp/xxx.html"
}
```

**响应**：
```json
{
    "success": true
}
```

---

## 4. CLI 接口

```bash
python main.py \
    --city "深圳" \
    --brands "优衣库,海底捞,星巴克" \
    --threshold 200 \
    --required-brands "海底捞" \
    --output json,log,html \
    --json-file result.json \
    --html-file map.html
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--city` | string | 是 | - | 城市名称 |
| `--brands` | string | 是 | - | 品牌列表（逗号分隔） |
| `--threshold` | float | 否 | 200 | 距离阈值（米） |
| `--required-brands` | string | 否 | - | 必选品牌（逗号分隔） |
| `--output` | string | 否 | json,log | 输出格式（json/log/html） |
| `--json-file` | string | 否 | 自动生成 | JSON 输出文件名 |
| `--html-file` | string | 否 | map.html | HTML 输出文件名 |

**退出码**：
- `0`：成功
- `1`：配置错误 / 参数错误 / 无结果
