"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 高德地图API密钥（从环境变量读取）
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")

# 高德地图API基础URL
AMAP_BASE_URL = "https://restapi.amap.com/v3"

# 默认距离阈值（单位：米）
DEFAULT_DISTANCE_THRESHOLD = int(os.getenv("DEFAULT_DISTANCE_THRESHOLD", "200"))

# 门店去重距离阈值（单位：米）
# 搜索品牌门店时，距离小于此值的门店认为是同一家店，会进行去重
DEDUPLICATION_DISTANCE = float(os.getenv("DEDUPLICATION_DISTANCE", "200"))

# POI搜索API端点
POI_SEARCH_ENDPOINT = "/place/text"

