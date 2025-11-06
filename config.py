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

# POI搜索API端点
POI_SEARCH_ENDPOINT = "/place/text"

