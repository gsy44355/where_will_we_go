# 核心算法设计

**版本**：v1.0
**最后更新**：2026-03-05

---

## 1. 距离计算

### 1.1 Haversine 公式

使用 Haversine 公式计算地球表面两点间的大圆距离。

**源文件**：`distance.py:haversine_distance()`

**公式**：
```
a = sin²(Δφ/2) + cos(φ₁) × cos(φ₂) × sin²(Δλ/2)
c = 2 × atan2(√a, √(1-a))
d = R × c
```

其中：
- `φ` = 纬度（弧度）
- `λ` = 经度（弧度）
- `R` = 地球半径 = 6,371,000 米

**复杂度**：O(1)

### 1.2 两两距离检查

**源文件**：`distance.py:check_all_distances(stores, threshold)`

给定 N 个门店，检查所有 C(N,2) 个门店对的距离是否均 ≤ 阈值。

**优化**：Early termination — 一旦发现某对距离超过阈值，立即返回 `(False, max_distance)`。

**复杂度**：O(N²)，最坏情况；实际通常因 early termination 提前退出。

### 1.3 最大距离计算

**源文件**：`distance.py:calculate_max_distance(stores)`

计算门店列表中所有门店对的最大距离。与 `check_all_distances` 类似，但不做 early termination。

---

## 2. 暴力算法

**源文件**：`cluster_finder.py:find_clusters()` 中 `use_optimized=False` 分支

### 2.1 全品牌组合

对 K 个品牌，每个品牌有 Nₖ 个门店，生成所有可能的组合（Cartesian product），逐一检查距离。

**总组合数**：N₁ × N₂ × ... × Nₖ

```python
for combination in product(*store_lists):
    is_valid, max_dist = check_all_distances(combination, threshold)
    if is_valid:
        valid_clusters.append(...)
```

**复杂度**：O(∏Nₖ × K²)

### 2.2 部分品牌回退

当全品牌组合无结果时，从 K 个品牌中枚举 r 个品牌的子集（r 从 K-1 递减到 2）。

```python
for r in range(len(valid_brands), min_r - 1, -1):
    for brand_subset in combinations(valid_brands, r):
        if required_brands and not all(rb in brand_subset for rb in required_brands):
            continue  # 跳过不含必选品牌的子集
        # 对子集执行 Cartesian product 检查
```

**min_r 确定**：
- 无必选品牌：`min_r = 2`
- 有必选品牌：`min_r = max(2, len(required_brands))`

---

## 3. 优化算法

**源文件**：`cluster_finder_optimized.py:find_clusters_optimized()`

### 3.1 空间网格索引 (SpatialGrid)

**源文件**：`cluster_finder_optimized.py:SpatialGrid`

将二维空间划分为网格单元，每个门店映射到一个网格。查找附近门店时只需检查 3×3 邻域。

**网格大小**：`grid_size = threshold × 2`

**坐标到网格的映射**：
```python
grid_lat = int(lat / (grid_size / 111000))        # 纬度方向
grid_lon = int(lon / (grid_size / (111000 × cos(radians(lat)))))  # 经度方向
```

其中 111,000 米 ≈ 1 个纬度的米数。经度方向需要用 `cos(lat)` 修正。

**查找附近门店**：
```python
for dlat in [-1, 0, 1]:
    for dlon in [-1, 0, 1]:
        check_key = (grid_lat + dlat, grid_lon + dlon)
        # 遍历该网格中的门店
        # 对每个门店做精确 Haversine 距离检查
```

**复杂度**：
- 构建索引：O(N)
- 查询附近：O(M)，M 为邻域内门店数（通常远小于 N）

### 3.2 候选集构建与剪枝

**思路**：对每个品牌的每个门店，预先计算其附近其他品牌的门店集合。

```python
brand_candidates[brand][store_idx] = {
    other_brand: [nearby_store_indices],
    ...
}
```

**剪枝效果**：只有空间上相邻的门店才会进入候选集，大量不可能的组合被提前排除。

**优化后组合数估算**：

```python
total_optimized = 0
for first_store in brand_to_indices[first_brand]:
    candidates = brand_candidates[first_brand][first_store]
    count = ∏ len(candidates[other_brand])  # 如果某品牌无候选则 count=0
    total_optimized += count
```

典型场景下减少 90%+ 的组合检查。

### 3.3 优化算法主流程

```
1. 构建所有门店索引映射
   all_stores[], brand_to_indices{}, store_to_brand{}

2. 构建空间索引
   SpatialGrid(all_stores, threshold)

3. 为每个品牌的门店构建候选集
   brand_candidates[brand][store_idx] = {other_brand: [indices]}

4. 查找全品牌商圈
   遍历第一个品牌的门店:
     检查是否所有其他品牌都有候选
     对候选组合做 check_all_distances()

5. 若无结果 → 部分品牌回退（同暴力算法逻辑）
   利用已有的候选集加速
```

---

## 4. 商圈去重

**源文件**：`cluster_finder.py:_deduplicate_clusters()`

### 4.1 问题

同一个门店可能出现在多个商圈中。需要保证每个门店只归属一个商圈。

### 4.2 贪心算法

```
1. 将所有商圈按 (brand_count 降序, max_distance 升序) 排序
2. 维护 used_stores 集合
3. 遍历排序后的商圈:
   - 提取该商圈所有门店的 key
   - 如果与 used_stores 有交集 → 跳过
   - 否则加入结果，更新 used_stores
```

**效果**：优先保留品牌数最多、距离最小的商圈。

### 4.3 门店唯一标识

```python
def _store_key(store):
    if store.get('poi_id'):
        return poi_id
    return f"{lat:.6f},{lon:.6f}"
```

---

## 5. 门店去重

**源文件**：`amap_api.py:deduplicate_stores()`

### 5.1 问题

高德 API 搜索结果中可能包含位置极近的同名门店（如同一家店在不同数据源中有多条记录）。

### 5.2 算法

```
对于每个未标记的门店 A:
  找出所有与 A 距离 < DEDUPLICATION_DISTANCE 的门店
  在这些门店中保留名称最长的（名称最完整）
  标记其余门店为已移除
```

**阈值**：`DEDUPLICATION_DISTANCE`，默认 200 米（可配置）。

**复杂度**：O(N²)

---

## 6. 必选品牌过滤

**作用位置**：部分品牌回退循环中

**逻辑**：

```python
# 确定最小品牌子集大小
min_r = max(2, len(required_brands)) if required_brands else 2

# 枚举子集时过滤
for brand_subset in combinations(valid_brands, r):
    if required_brands and not all(rb in brand_subset for rb in required_brands):
        continue  # 子集不包含所有必选品牌，跳过
```

**边界情况**：
- `required_brands` 为 None 或空：不做过滤，行为不变
- 所有品牌都标记为必选：等价于不设必选（只有全集才满足）
- 必选品牌对应的品牌未搜索到门店：自动从必选列表移除

---

## 7. 算法复杂度总结

| 操作 | 暴力算法 | 优化算法 |
|------|----------|----------|
| 空间索引构建 | - | O(N) |
| 候选集构建 | - | O(N × M) |
| 全品牌组合 | O(∏Nₖ × K²) | O(优化组合数 × K²) |
| 部分品牌回退 | O(∑C(K,r) × ∏Nₖ) | 同上，利用候选集 |
| 商圈去重 | O(C × log C) | 同 |

其中 N = 总门店数，K = 品牌数，M = 平均邻域门店数，C = 候选商圈数。
