"""
优化的商圈查找算法 - 使用空间索引和早期剪枝
"""
from typing import List, Dict, Tuple, Set
from itertools import product
import math
from collections import defaultdict
from tqdm import tqdm
from distance import haversine_distance, check_all_distances


class SpatialGrid:
    """简单的空间网格索引，用于快速查找附近的门店"""
    
    def __init__(self, stores: List[Dict], threshold: float):
        """
        初始化空间网格
        
        Args:
            stores: 门店列表
            threshold: 距离阈值
        """
        self.threshold = threshold
        self.grid_size = threshold * 2  # 网格大小设为阈值的2倍
        self.grid = defaultdict(list)
        self.stores = stores
        
        # 将门店放入网格
        for idx, store in enumerate(stores):
            grid_key = self._get_grid_key(store["lat"], store["lon"])
            self.grid[grid_key].append(idx)
    
    def _get_grid_key(self, lat: float, lon: float) -> Tuple[int, int]:
        """获取门店所在的网格坐标"""
        grid_lat = int(lat / (self.grid_size / 111000))  # 大约111km每度
        grid_lon = int(lon / (self.grid_size / (111000 * math.cos(math.radians(lat)))))
        return (grid_lat, grid_lon)
    
    def get_nearby_stores(self, store_idx: int) -> Set[int]:
        """
        获取指定门店附近的所有门店索引
        
        Args:
            store_idx: 门店索引
        
        Returns:
            附近门店索引集合
        """
        store = self.stores[store_idx]
        grid_key = self._get_grid_key(store["lat"], store["lon"])
        
        nearby = set()
        # 检查当前网格和相邻8个网格
        for dlat in [-1, 0, 1]:
            for dlon in [-1, 0, 1]:
                check_key = (grid_key[0] + dlat, grid_key[1] + dlon)
                if check_key in self.grid:
                    for other_idx in self.grid[check_key]:
                        if other_idx != store_idx:
                            # 精确距离检查
                            other_store = self.stores[other_idx]
                            dist = haversine_distance(
                                store["lat"], store["lon"],
                                other_store["lat"], other_store["lon"]
                            )
                            if dist <= self.threshold:
                                nearby.add(other_idx)
        
        return nearby


def find_clusters_optimized(brand_stores_dict: Dict[str, List[Dict]], threshold: float) -> List[Dict]:
    """
    优化的商圈查找算法
    
    使用空间索引和候选集过滤大幅减少需要检查的组合数
    
    Args:
        brand_stores_dict: 字典，键为品牌名，值为该品牌的门店列表
        threshold: 距离阈值（米）
    
    Returns:
        符合条件的商圈列表
    """
    brands = list(brand_stores_dict.keys())
    valid_brands = [brand for brand in brands if brand_stores_dict[brand]]
    
    if not valid_brands:
        return []
    
    if len(valid_brands) == 1:
        brand = valid_brands[0]
        clusters = []
        for store in brand_stores_dict[brand]:
            clusters.append({
                "brands": {brand: store},
                "stores": [store],
                "max_distance": 0.0,
                "brand_count": 1
            })
        return clusters
    
    # 构建所有门店的索引映射
    all_stores = []
    brand_to_indices = {}
    store_to_brand = {}
    
    for brand in valid_brands:
        brand_indices = []
        for store in brand_stores_dict[brand]:
            idx = len(all_stores)
            all_stores.append(store)
            brand_indices.append(idx)
            store_to_brand[idx] = brand
        brand_to_indices[brand] = brand_indices
    
    # 构建空间索引
    print("  构建空间索引...")
    spatial_grid = SpatialGrid(all_stores, threshold)
    
    # 为每个品牌的门店构建候选集（只包含其他品牌的门店）
    print("  构建候选集...")
    brand_candidates = {}
    total_original = math.prod(len(brand_stores_dict[b]) for b in valid_brands)
    
    for brand in valid_brands:
        brand_candidates[brand] = {}
        for store_idx in tqdm(brand_to_indices[brand], desc=f"  处理{brand}", leave=False, unit="门店"):
            nearby = spatial_grid.get_nearby_stores(store_idx)
            # 按品牌分组
            candidates_by_brand = defaultdict(list)
            for other_idx in nearby:
                other_brand = store_to_brand[other_idx]
                if other_brand != brand:
                    candidates_by_brand[other_brand].append(other_idx)
            brand_candidates[brand][store_idx] = candidates_by_brand
    
    # 计算优化后的组合数
    total_optimized = 0
    for first_store_idx in brand_to_indices[valid_brands[0]]:
        candidates = brand_candidates[valid_brands[0]][first_store_idx]
        if not candidates:
            continue
        count = 1
        for other_brand in valid_brands[1:]:
            if other_brand in candidates:
                count *= len(candidates[other_brand])
            else:
                count = 0
                break
        total_optimized += count
    
    print(f"  原始组合数: {total_original:,}")
    print(f"  优化后组合数: {total_optimized:,}")
    if total_optimized > 0:
        reduction = (1 - total_optimized / total_original) * 100
        print(f"  减少: {reduction:.1f}%")
    
    # 使用优化的候选集查找商圈
    print("  查找商圈...")
    valid_clusters = []
    
    # 从第一个品牌开始
    first_brand = valid_brands[0]
    
    # 遍历第一个品牌的所有门店
    for first_store_idx in tqdm(brand_to_indices[first_brand], desc="  查找商圈", unit="门店"):
        candidates = brand_candidates[first_brand][first_store_idx]
        
        # 检查是否所有其他品牌都有候选门店
        if not all(brand in candidates for brand in valid_brands[1:]):
            continue
        
        # 生成候选组合
        candidate_lists = [candidates[brand] for brand in valid_brands[1:]]
        
        for combination in product(*candidate_lists):
            # 构建完整的门店列表
            store_indices = [first_store_idx] + list(combination)
            stores = [all_stores[idx] for idx in store_indices]
            
            # 检查距离
            is_valid, max_dist = check_all_distances(stores, threshold)
            
            if is_valid:
                brands_dict = {}
                for idx in store_indices:
                    brand = store_to_brand[idx]
                    brands_dict[brand] = all_stores[idx]
                
                cluster = {
                    "brands": brands_dict,
                    "stores": stores,
                    "max_distance": max_dist,
                    "brand_count": len(valid_brands)
                }
                valid_clusters.append(cluster)
    
    # 如果找到全部品牌满足的，直接返回
    if valid_clusters:
        return valid_clusters
    
    # 如果没有完全符合条件的，尝试部分品牌组合
    # 收集所有符合条件的商圈，优先返回品牌数多的
    print("  未找到完全符合条件的商圈，查找部分品牌组合...")
    from itertools import combinations
    
    all_partial_clusters = []
    max_brand_count = 0
    
    # 从多到少尝试品牌组合（至少2个品牌）
    # 查找所有符合条件的商圈，不提前结束
    for r in range(len(valid_brands), 1, -1):
        if r < 2:  # 至少包含2个品牌
            break
        
        clusters_found = False
        for brand_subset in combinations(valid_brands, r):
            first_brand_sub = brand_subset[0]
            
            for first_store_idx in brand_to_indices[first_brand_sub]:
                candidates = brand_candidates[first_brand_sub][first_store_idx]
                
                if not all(brand in candidates for brand in brand_subset[1:]):
                    continue
                
                candidate_lists = [candidates[brand] for brand in brand_subset[1:]]
                
                for combination in product(*candidate_lists):
                    store_indices = [first_store_idx] + list(combination)
                    stores = [all_stores[idx] for idx in store_indices]
                    
                    is_valid, max_dist = check_all_distances(stores, threshold)
                    
                    if is_valid:
                        brands_dict = {}
                        for idx in store_indices:
                            brand = store_to_brand[idx]
                            brands_dict[brand] = all_stores[idx]
                        
                        cluster = {
                            "brands": brands_dict,
                            "stores": stores,
                            "max_distance": max_dist,
                            "brand_count": len(brand_subset)
                        }
                        all_partial_clusters.append(cluster)
                        max_brand_count = max(max_brand_count, len(brand_subset))
                        clusters_found = True
        
        # 如果找到了当前品牌数的商圈，继续查找（可能还有其他组合）
        if clusters_found:
            print(f"  找到 {len([c for c in all_partial_clusters if c['brand_count'] == r])} 个包含 {r} 个品牌的商圈")
    
    # 按品牌数量降序排序，返回所有结果
    if all_partial_clusters:
        all_partial_clusters.sort(key=lambda x: x['brand_count'], reverse=True)
        print(f"  共找到 {len(all_partial_clusters)} 个符合条件的商圈（至少2个品牌）")
        return all_partial_clusters
    
    return []

