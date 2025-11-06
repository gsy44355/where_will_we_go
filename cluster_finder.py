"""
商圈查找核心算法
"""
from typing import List, Dict, Tuple
from itertools import product
import math
from tqdm import tqdm
from distance import check_all_distances, calculate_max_distance


def find_clusters(brand_stores_dict: Dict[str, List[Dict]], threshold: float) -> List[Dict]:
    """
    查找所有符合条件的商圈
    
    商圈定义：每个品牌至少有一个门店，且这些门店之间两两距离都小于阈值
    
    Args:
        brand_stores_dict: 字典，键为品牌名，值为该品牌的门店列表
        threshold: 距离阈值（米）
    
    Returns:
        符合条件的商圈列表，如果没有完全符合条件的，返回覆盖品牌最多的组合
    """
    brands = list(brand_stores_dict.keys())
    
    # 过滤掉没有门店的品牌
    valid_brands = [brand for brand in brands if brand_stores_dict[brand]]
    
    if not valid_brands:
        return []
    
    if len(valid_brands) == 1:
        # 只有一个品牌，返回所有门店作为独立商圈
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
    
    # 生成所有可能的门店组合（每个品牌选一个门店）
    store_lists = [brand_stores_dict[brand] for brand in valid_brands]
    
    # 计算总组合数
    total_combinations = math.prod(len(stores) for stores in store_lists)
    
    # 显示详细信息
    print(f"  品牌数量: {len(valid_brands)}")
    print(f"  各品牌门店数: {', '.join(f'{brand}({len(stores)})' for brand, stores in zip(valid_brands, store_lists))}")
    print(f"  总组合数: {total_combinations:,}")
    
    # 预估时间（假设每个组合检查需要约0.001秒）
    estimated_seconds = total_combinations * 0.001
    if estimated_seconds < 60:
        time_str = f"{estimated_seconds:.1f} 秒"
    elif estimated_seconds < 3600:
        time_str = f"{estimated_seconds/60:.1f} 分钟"
    else:
        time_str = f"{estimated_seconds/3600:.1f} 小时"
    
    if total_combinations > 1000000:
        print(f"  预估时间: {time_str}（组合数量较大，可能需要较长时间）")
    elif total_combinations > 100000:
        print(f"  预估时间: {time_str}")
    
    valid_clusters = []
    best_partial_cluster = None
    best_brand_count = 0
    
    # 遍历所有可能的组合，显示进度条
    for combination in tqdm(product(*store_lists), total=total_combinations, desc="  查找商圈", unit="组合", ncols=100):
        stores = list(combination)
        
        # 检查所有门店之间两两距离是否都小于阈值
        is_valid, max_dist = check_all_distances(stores, threshold)
        
        if is_valid:
            # 完全符合条件的商圈
            cluster = {
                "brands": {valid_brands[i]: stores[i] for i in range(len(valid_brands))},
                "stores": stores,
                "max_distance": max_dist,
                "brand_count": len(valid_brands)
            }
            valid_clusters.append(cluster)
        else:
            # 记录部分匹配的结果（覆盖品牌最多的）
            if len(valid_brands) > best_brand_count:
                best_brand_count = len(valid_brands)
                best_partial_cluster = {
                    "brands": {valid_brands[i]: stores[i] for i in range(len(valid_brands))},
                    "stores": stores,
                    "max_distance": max_dist,
                    "brand_count": len(valid_brands)
                }
    
    # 如果有完全符合条件的商圈，返回它们
    if valid_clusters:
        return valid_clusters
    
    # 如果没有完全符合条件的，尝试找部分品牌组合
    # 尝试所有可能的品牌子集组合
    from itertools import combinations
    
    if not valid_clusters:
        print(f"  未找到完全符合条件的商圈，尝试部分品牌组合...")
        
        # 计算部分组合的总数
        total_partial_combinations = 0
        for r in range(len(valid_brands), 1, -1):
            for brand_subset in combinations(valid_brands, r):
                store_lists_subset = [brand_stores_dict[brand] for brand in brand_subset]
                total_partial_combinations += math.prod(len(stores) for stores in store_lists_subset)
        
        if total_partial_combinations > 0:
            print(f"  需要检查 {total_partial_combinations:,} 个部分品牌组合...")
    
    for r in range(len(valid_brands), 1, -1):
        for brand_subset in combinations(valid_brands, r):
            store_lists_subset = [brand_stores_dict[brand] for brand in brand_subset]
            subset_total = math.prod(len(stores) for stores in store_lists_subset)
            
            brand_names = ', '.join(brand_subset)
            if len(brand_names) > 30:
                brand_names = brand_names[:27] + "..."
            desc = f"  检查 {len(brand_subset)} 个品牌"
            for combination in tqdm(product(*store_lists_subset), total=subset_total, desc=desc, unit="组合", leave=False, ncols=100, postfix=brand_names):
                stores = list(combination)
                is_valid, max_dist = check_all_distances(stores, threshold)
                
                if is_valid:
                    cluster = {
                        "brands": {brand_subset[i]: stores[i] for i in range(len(brand_subset))},
                        "stores": stores,
                        "max_distance": max_dist,
                        "brand_count": len(brand_subset)
                    }
                    valid_clusters.append(cluster)
        
        # 如果找到了部分匹配的商圈，返回它们
        if valid_clusters:
            return valid_clusters
    
    # 如果完全没有符合条件的，返回覆盖品牌最多的单个组合
    if best_partial_cluster:
        return [best_partial_cluster]
    
    return []

