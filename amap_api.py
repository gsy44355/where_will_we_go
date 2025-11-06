"""
高德地图API封装模块
"""
import requests
import time
from typing import List, Dict, Optional
from config import AMAP_API_KEY, AMAP_BASE_URL, POI_SEARCH_ENDPOINT

# API限流配置
REQUEST_DELAY = 0.2  # 每次请求之间的延迟（秒）
RATE_LIMIT_RETRY_DELAY = 2.0  # 遇到限流时的重试延迟（秒）
MAX_RETRIES = 3  # 最大重试次数


def search_poi(city: str, keyword: str, max_pages: int = 10) -> List[Dict]:
    """
    搜索城市内指定关键词的POI
    
    Args:
        city: 城市名称
        keyword: 搜索关键词（品牌名称）
        max_pages: 最大搜索页数（每页20条）
    
    Returns:
        门店列表，每个门店包含：name, address, lat, lon
    """
    stores = []
    page = 1
    
    while page <= max_pages:
        retry_count = 0
        success = False
        
        while retry_count <= MAX_RETRIES and not success:
            try:
                url = f"{AMAP_BASE_URL}{POI_SEARCH_ENDPOINT}"
                params = {
                    "key": AMAP_API_KEY,
                    "keywords": keyword,
                    "city": city,
                    "offset": 20,  # 每页20条
                    "page": page,
                    "extensions": "all"  # 返回详细信息
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # 检查API返回状态
                if data.get("status") != "1":
                    error_msg = data.get("info", "未知错误")
                    error_code = data.get("infocode", "")
                    
                    # 处理限流错误
                    if "CUQPS_HAS_EXCEEDED_THE_LIMIT" in error_msg or error_code == "10009":
                        if retry_count < MAX_RETRIES:
                            wait_time = RATE_LIMIT_RETRY_DELAY * (retry_count + 1)
                            print(f"遇到API限流，等待 {wait_time:.1f} 秒后重试... (第 {retry_count + 1}/{MAX_RETRIES} 次)")
                            time.sleep(wait_time)
                            retry_count += 1
                            continue
                        else:
                            print(f"警告: 搜索 {keyword} 第 {page} 页时达到最大重试次数，跳过")
                            break
                    else:
                        # 其他错误，直接退出
                        print(f"警告: 搜索 {keyword} 时出错 - {error_msg}")
                        break
                
                # 成功获取数据
                success = True
                pois = data.get("pois", [])
                if not pois:
                    # 没有更多数据，退出外层循环
                    page = max_pages + 1
                    break
                
                # 解析POI数据
                for poi in pois:
                    location = poi.get("location", "").split(",")
                    if len(location) == 2:
                        store = {
                            "name": poi.get("name", ""),
                            "address": poi.get("address", ""),
                            "lat": float(location[1]),  # 纬度
                            "lon": float(location[0]),  # 经度
                            "poi_id": poi.get("id", ""),
                            "type": poi.get("type", "")
                        }
                        stores.append(store)
                
                # 检查是否还有更多数据
                count = int(data.get("count", 0))
                if len(stores) >= count or len(pois) < 20:
                    # 没有更多数据，退出外层循环
                    page = max_pages + 1
                    break
                
                page += 1
                # 请求之间的延迟，避免触发限流
                time.sleep(REQUEST_DELAY)
                # 成功获取数据后，退出重试循环，继续下一页
                break
                
            except requests.exceptions.RequestException as e:
                if retry_count < MAX_RETRIES:
                    wait_time = RATE_LIMIT_RETRY_DELAY * (retry_count + 1)
                    print(f"网络请求失败，等待 {wait_time:.1f} 秒后重试... (第 {retry_count + 1}/{MAX_RETRIES} 次)")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                else:
                    print(f"错误: 请求高德地图API失败 - {e}")
                    break
            except Exception as e:
                print(f"错误: 处理API响应时出错 - {e}")
                break
        
        # 如果重试失败，退出循环
        if not success:
            break
    
    print(f"找到 {keyword} 在 {city} 的 {len(stores)} 个门店")
    return stores


def search_brands(city: str, brands: List[str]) -> Dict[str, List[Dict]]:
    """
    搜索多个品牌的门店
    
    Args:
        city: 城市名称
        brands: 品牌名称列表
    
    Returns:
        字典，键为品牌名，值为该品牌的门店列表
    """
    brand_stores = {}
    
    for idx, brand in enumerate(brands):
        stores = search_poi(city, brand)
        if stores:
            brand_stores[brand] = stores
        else:
            print(f"警告: 未找到 {brand} 在 {city} 的门店")
            brand_stores[brand] = []
        
        # 品牌之间的延迟，避免触发限流
        if idx < len(brands) - 1:  # 最后一个品牌不需要延迟
            time.sleep(REQUEST_DELAY * 2)  # 品牌之间延迟稍长一些
    
    return brand_stores

