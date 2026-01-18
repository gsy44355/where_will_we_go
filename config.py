"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 高德地图API密钥（从环境变量读取）
# REST API 密钥（用于POI搜索等服务端API）
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")

# JS API 密钥（用于Web端地图显示，如果不设置则使用REST API密钥）
AMAP_JS_KEY = os.getenv("AMAP_JS_KEY", "") or AMAP_API_KEY

# JS API 安全密钥（高德地图JS API 2.0必须配置，否则地图无法显示）
# 需要在高德开放平台控制台创建Web端(JS API)类型的Key，并获取安全密钥
AMAP_SECURITY_CODE = os.getenv("AMAP_SECURITY_CODE", "")

# 高德地图API基础URL
AMAP_BASE_URL = "https://restapi.amap.com/v3"

# 默认距离阈值（单位：米）
DEFAULT_DISTANCE_THRESHOLD = int(os.getenv("DEFAULT_DISTANCE_THRESHOLD", "200"))

# 门店去重距离阈值（单位：米）
# 搜索品牌门店时，距离小于此值的门店认为是同一家店，会进行去重
DEDUPLICATION_DISTANCE = float(os.getenv("DEDUPLICATION_DISTANCE", "200"))

# POI搜索API端点
POI_SEARCH_ENDPOINT = "/place/text"

