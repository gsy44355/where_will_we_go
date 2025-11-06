"""
距离计算模块 - 使用Haversine公式计算地球表面两点间距离
"""
import math
from typing import List, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    使用Haversine公式计算两点间的大圆距离（单位：米）
    
    Args:
        lat1: 第一个点的纬度
        lon1: 第一个点的经度
        lat2: 第二个点的纬度
        lon2: 第二个点的经度
    
    Returns:
        两点间的距离（米）
    """
    # 地球半径（米）
    R = 6371000
    
    # 将角度转换为弧度
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine公式
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def check_all_distances(stores: List[dict], threshold: float) -> Tuple[bool, float]:
    """
    检查门店列表中所有门店之间两两距离是否都小于阈值
    
    Args:
        stores: 门店列表，每个门店包含 lat 和 lon
        threshold: 距离阈值（米）
    
    Returns:
        (是否满足条件, 最大距离)
    """
    if len(stores) < 2:
        return True, 0.0
    
    max_distance = 0.0
    
    for i in range(len(stores)):
        for j in range(i + 1, len(stores)):
            store1 = stores[i]
            store2 = stores[j]
            distance = haversine_distance(
                store1["lat"], store1["lon"],
                store2["lat"], store2["lon"]
            )
            max_distance = max(max_distance, distance)
            
            if distance > threshold:
                return False, max_distance
    
    return True, max_distance


def calculate_max_distance(stores: List[dict]) -> float:
    """
    计算门店列表中的最大距离
    
    Args:
        stores: 门店列表
    
    Returns:
        最大距离（米）
    """
    if len(stores) < 2:
        return 0.0
    
    max_distance = 0.0
    for i in range(len(stores)):
        for j in range(i + 1, len(stores)):
            distance = haversine_distance(
                stores[i]["lat"], stores[i]["lon"],
                stores[j]["lat"], stores[j]["lon"]
            )
            max_distance = max(max_distance, distance)
    
    return max_distance

