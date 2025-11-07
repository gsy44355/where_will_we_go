"""
结果输出模块
"""
import json
from typing import List, Dict
from datetime import datetime
from config import AMAP_API_KEY


def output_json(clusters: List[Dict], filename: str = None) -> str:
    """
    生成JSON格式结果
    
    Args:
        clusters: 商圈列表
        filename: 输出文件名（可选，如果为None则返回JSON字符串）
    
    Returns:
        JSON字符串
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "cluster_count": len(clusters),
        "clusters": clusters
    }
    
    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"JSON结果已保存到: {filename}")
    
    return json_str


def output_log(clusters: List[Dict]):
    """
    命令行日志输出
    
    Args:
        clusters: 商圈列表
    """
    print("\n" + "=" * 60)
    print("商圈查找结果")
    print("=" * 60)
    
    if not clusters:
        print("未找到符合条件的商圈")
        return
    
    print(f"\n找到 {len(clusters)} 个符合条件的商圈：\n")
    
    for idx, cluster in enumerate(clusters, 1):
        print(f"商圈 #{idx}")
        print("-" * 40)
        print(f"包含品牌数: {cluster.get('brand_count', len(cluster['brands']))}")
        print(f"最大距离: {cluster['max_distance']:.2f} 米")
        print("\n门店信息:")
        
        for brand, store in cluster["brands"].items():
            print(f"  [{brand}]")
            print(f"    名称: {store['name']}")
            print(f"    地址: {store['address']}")
            print(f"    坐标: ({store['lat']:.6f}, {store['lon']:.6f})")
        
        print()
    
    print("=" * 60)


def output_html(clusters: List[Dict], city: str, filename: str = "map.html"):
    """
    生成HTML地图文件（使用高德地图JS API）
    
    Args:
        clusters: 商圈列表
        city: 城市名称
        filename: 输出文件名
    """
    # 生成标记点数据
    markers_data = []
    for idx, cluster in enumerate(clusters):
        cluster_markers = []
        for brand, store in cluster["brands"].items():
            cluster_markers.append({
                "name": store["name"],
                "address": store["address"],
                "lat": store["lat"],
                "lon": store["lon"],
                "brand": brand
            })
        markers_data.append({
            "cluster_id": idx + 1,
            "max_distance": cluster["max_distance"],
            "brand_count": cluster.get("brand_count", len(cluster["brands"])),
            "markers": cluster_markers
        })
    
    # 计算地图中心点（所有门店的平均坐标）
    if clusters:
        all_lats = []
        all_lons = []
        for cluster in clusters:
            for store in cluster["stores"]:
                all_lats.append(store["lat"])
                all_lons.append(store["lon"])
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
    else:
        center_lat = 39.9042  # 北京默认坐标
        center_lon = 116.4074
    
    # 准备JavaScript数据
    clusters_json = json.dumps(markers_data, ensure_ascii=False)
    
    # 生成HTML内容 - 使用字符串拼接避免f-string转义问题
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>商圈地图 - """ + city + """</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
        #mapContainer {
            width: 100%;
            height: 100vh;
        }
        #infoPanel {
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 300px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 1000;
        }
        .cluster-info {
            margin-bottom: 15px;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: white;
        }
        .cluster-info:hover {
            border-color: #0066cc;
            box-shadow: 0 2px 8px rgba(0,102,204,0.3);
            transform: translateY(-2px);
        }
        .cluster-info.active {
            border-color: #0066cc;
            background: #f0f7ff;
            box-shadow: 0 2px 8px rgba(0,102,204,0.5);
        }
        .cluster-info h3 {
            margin: 0 0 8px 0;
            color: #333;
            font-size: 16px;
        }
        .store-item {
            margin: 5px 0;
            padding: 6px 8px;
            background: #f5f5f5;
            border-radius: 3px;
            font-size: 12px;
            border-left: 3px solid transparent;
        }
        .store-item:hover {
            background: #e8f4ff;
            border-left-color: #0066cc;
        }
        .store-brand {
            font-weight: bold;
            color: #0066cc;
        }
    </style>
</head>
<body>
    <div id="mapContainer"></div>
    <div id="infoPanel">
        <h2>商圈信息</h2>
        <p>城市: """ + city + """</p>
        <p>找到 """ + str(len(clusters)) + """ 个商圈</p>
        <div id="clusterList"></div>
    </div>
    
    <script src="https://webapi.amap.com/maps?v=2.0&key=""" + AMAP_API_KEY + """"></script>
    <script>
        // 商圈数据
        const clusters = """ + clusters_json + """;
        const center = [""" + str(center_lon) + """, """ + str(center_lat) + """];
        
        // 初始化地图
        const map = new AMap.Map('mapContainer', {
            zoom: 13,
            center: center,
            mapStyle: 'amap://styles/normal'
        });
        
        // 颜色列表（用于区分不同商圈）
        const colors = ['#FF4444', '#44AA44', '#4444FF', '#FFAA00', '#AA44FF', '#00AAAA', '#FF8800', '#8844AA'];
        const clusterGroups = []; // 存储每个商圈的标记组和连接线
        
        // 创建自定义图标函数
        function createCustomIcon(color, label) {
            const size = 40;
            const svg = `
                <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="${size/2}" cy="${size/2}" r="${size/2 - 2}" fill="${color}" stroke="white" stroke-width="2" opacity="0.9"/>
                    <text x="${size/2}" y="${size/2 + 5}" font-family="Arial" font-size="14" font-weight="bold" fill="white" text-anchor="middle">${label}</text>
                </svg>
            `;
            const iconUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
            return new AMap.Icon({
                image: iconUrl,
                size: new AMap.Size(size, size),
                imageSize: new AMap.Size(size, size)
            });
        }
        
        // 为每个商圈创建标记和信息窗口
        clusters.forEach((cluster, clusterIdx) => {
            const color = colors[clusterIdx % colors.length];
            const clusterGroup = {
                markers: [],
                polyline: null,
                infoDiv: null,
                clusterId: cluster.cluster_id
            };
            
            // 创建该商圈的所有标记
            cluster.markers.forEach((markerData, markerIdx) => {
                const label = markerIdx + 1;
                const marker = new AMap.Marker({
                    position: [markerData.lon, markerData.lat],
                    title: markerData.name,
                    icon: createCustomIcon(color, label),
                    zIndex: 100 + clusterIdx
                });
                
                const infoWindow = new AMap.InfoWindow({
                    content: `
                        <div style="padding: 10px; min-width: 200px;">
                            <h3 style="margin: 0 0 10px 0; color: ${color}; border-bottom: 2px solid ${color}; padding-bottom: 5px;">${markerData.name}</h3>
                            <p style="margin: 5px 0;"><strong>品牌:</strong> <span style="color: ${color}; font-weight: bold;">${markerData.brand}</span></p>
                            <p style="margin: 5px 0;"><strong>地址:</strong> ${markerData.address}</p>
                            <p style="margin: 5px 0; color: #666; font-size: 12px;">商圈 #${cluster.cluster_id} - 门店 ${label}/${cluster.markers.length}</p>
                        </div>
                    `,
                    offset: new AMap.Pixel(0, -30)
                });
                
                marker.on('click', function() {
                    infoWindow.open(map, marker.getPosition());
                    // 高亮显示该商圈
                    highlightCluster(clusterIdx);
                });
                
                map.add(marker);
                clusterGroup.markers.push(marker);
            });
            
            // 如果商圈有多个门店，绘制连接线
            if (cluster.markers.length > 1) {
                const path = cluster.markers.map(m => [m.lon, m.lat]);
                const polyline = new AMap.Polyline({
                    path: path,
                    strokeColor: color,
                    strokeWeight: 4,
                    strokeOpacity: 0.7,
                    strokeStyle: 'solid',
                    zIndex: 10 + clusterIdx
                });
                map.add(polyline);
                clusterGroup.polyline = polyline;
            }
            
            // 添加商圈信息到侧边栏
            const clusterDiv = document.createElement('div');
            clusterDiv.className = 'cluster-info';
            clusterDiv.dataset.clusterIndex = clusterIdx;
            clusterDiv.innerHTML = `
                <h3 style="color: ${color}; border-left: 4px solid ${color}; padding-left: 8px;">商圈 #${cluster.cluster_id}</h3>
                <p style="margin: 5px 0; font-size: 13px;"><strong>品牌数:</strong> ${cluster.brand_count}</p>
                <p style="margin: 5px 0; font-size: 13px;"><strong>最大距离:</strong> ${cluster.max_distance.toFixed(2)} 米</p>
                <div style="margin-top: 10px;">
                    ${cluster.markers.map((m, idx) => `
                        <div class="store-item">
                            <span class="store-brand">[${m.brand}]</span> ${m.name}
                        </div>
                    `).join('')}
                </div>
            `;
            
            // 点击侧边栏卡片时，跳转到地图并高亮
            clusterDiv.addEventListener('click', function() {
                highlightCluster(clusterIdx);
                // 计算商圈中心点
                const lats = cluster.markers.map(m => m.lat);
                const lons = cluster.markers.map(m => m.lon);
                const centerLat = lats.reduce((a, b) => a + b) / lats.length;
                const centerLon = lons.reduce((a, b) => a + b) / lons.length;
                
                // 跳转到商圈位置
                map.setZoomAndCenter(15, [centerLon, centerLat]);
                
                // 打开第一个标记的信息窗口
                if (clusterGroup.markers.length > 0) {
                    const firstMarker = clusterGroup.markers[0];
                    const markerData = cluster.markers[0];
                    const infoWindow = new AMap.InfoWindow({
                        content: `
                            <div style="padding: 10px; min-width: 200px;">
                                <h3 style="margin: 0 0 10px 0; color: ${color}; border-bottom: 2px solid ${color}; padding-bottom: 5px;">${markerData.name}</h3>
                                <p style="margin: 5px 0;"><strong>品牌:</strong> <span style="color: ${color}; font-weight: bold;">${markerData.brand}</span></p>
                                <p style="margin: 5px 0;"><strong>地址:</strong> ${markerData.address}</p>
                                <p style="margin: 5px 0; color: #666; font-size: 12px;">商圈 #${cluster.cluster_id}</p>
                            </div>
                        `,
                        offset: new AMap.Pixel(0, -30)
                    });
                    infoWindow.open(map, firstMarker.getPosition());
                }
            });
            
            document.getElementById('clusterList').appendChild(clusterDiv);
            clusterGroup.infoDiv = clusterDiv;
            clusterGroups.push(clusterGroup);
        });
        
        // 高亮显示指定商圈
        function highlightCluster(clusterIdx) {
            // 移除所有高亮
            document.querySelectorAll('.cluster-info').forEach(div => {
                div.classList.remove('active');
            });
            
            // 高亮选中的商圈
            if (clusterGroups[clusterIdx] && clusterGroups[clusterIdx].infoDiv) {
                clusterGroups[clusterIdx].infoDiv.classList.add('active');
                // 滚动到可见区域
                clusterGroups[clusterIdx].infoDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        
        // 调整地图视野以包含所有标记
        if (clusters.length > 0) {
            const allPoints = [];
            clusters.forEach(cluster => {
                cluster.markers.forEach(m => {
                    allPoints.push([m.lon, m.lat]);
                });
            });
            map.setFitView(null, false, [100, 100, 100, 100]);
        }
    </script>
</body>
</html>"""
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML地图已保存到: {filename}")
    if not AMAP_API_KEY or AMAP_API_KEY == "your_api_key_here":
        print("警告: 请在 .env 文件中配置高德地图API密钥，否则HTML地图可能无法正常显示")
    
    return html_content


def output_html_string(clusters: List[Dict], city: str) -> str:
    """
    生成HTML地图字符串（用于web服务）
    
    Args:
        clusters: 商圈列表
        city: 城市名称
    
    Returns:
        HTML字符串
    """
    # 生成标记点数据
    markers_data = []
    for idx, cluster in enumerate(clusters):
        cluster_markers = []
        for brand, store in cluster["brands"].items():
            cluster_markers.append({
                "name": store["name"],
                "address": store["address"],
                "lat": store["lat"],
                "lon": store["lon"],
                "brand": brand
            })
        markers_data.append({
            "cluster_id": idx + 1,
            "max_distance": cluster["max_distance"],
            "brand_count": cluster.get("brand_count", len(cluster["brands"])),
            "markers": cluster_markers
        })
    
    # 计算地图中心点（所有门店的平均坐标）
    if clusters:
        all_lats = []
        all_lons = []
        for cluster in clusters:
            for store in cluster["stores"]:
                all_lats.append(store["lat"])
                all_lons.append(store["lon"])
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
    else:
        center_lat = 39.9042  # 北京默认坐标
        center_lon = 116.4074
    
    # 准备JavaScript数据
    clusters_json = json.dumps(markers_data, ensure_ascii=False)
    
    # 生成HTML内容 - 使用字符串拼接避免f-string转义问题
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>商圈地图 - """ + city + """</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        #mapContainer {
            width: 100%;
            height: 100vh;
        }
        #infoPanel {
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            max-width: 300px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 1000;
        }
        @media (max-width: 768px) {
            #infoPanel {
                position: fixed;
                top: auto;
                bottom: 0;
                right: 0;
                left: 0;
                max-width: 100%;
                max-height: 40vh;
                border-radius: 15px 15px 0 0;
            }
        }
        .cluster-info {
            margin-bottom: 15px;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: white;
        }
        .cluster-info:hover {
            border-color: #0066cc;
            box-shadow: 0 2px 8px rgba(0,102,204,0.3);
            transform: translateY(-2px);
        }
        .cluster-info.active {
            border-color: #0066cc;
            background: #f0f7ff;
            box-shadow: 0 2px 8px rgba(0,102,204,0.5);
        }
        .cluster-info h3 {
            margin: 0 0 8px 0;
            color: #333;
            font-size: 16px;
        }
        .store-item {
            margin: 5px 0;
            padding: 6px 8px;
            background: #f5f5f5;
            border-radius: 3px;
            font-size: 12px;
            border-left: 3px solid transparent;
        }
        .store-item:hover {
            background: #e8f4ff;
            border-left-color: #0066cc;
        }
        .store-brand {
            font-weight: bold;
            color: #0066cc;
        }
    </style>
</head>
<body>
    <div id="mapContainer"></div>
    <div id="infoPanel">
        <h2>商圈信息</h2>
        <p>城市: """ + city + """</p>
        <p>找到 """ + str(len(clusters)) + """ 个商圈</p>
        <div id="clusterList"></div>
    </div>
    
    <script src="https://webapi.amap.com/maps?v=2.0&key=""" + AMAP_API_KEY + """"></script>
    <script>
        // 商圈数据
        const clusters = """ + clusters_json + """;
        const center = [""" + str(center_lon) + """, """ + str(center_lat) + """];
        
        // 初始化地图
        const map = new AMap.Map('mapContainer', {
            zoom: 13,
            center: center,
            mapStyle: 'amap://styles/normal'
        });
        
        // 颜色列表（用于区分不同商圈）
        const colors = ['#FF4444', '#44AA44', '#4444FF', '#FFAA00', '#AA44FF', '#00AAAA', '#FF8800', '#8844AA'];
        const clusterGroups = []; // 存储每个商圈的标记组和连接线
        
        // 创建自定义图标函数
        function createCustomIcon(color, label) {
            const size = 40;
            const svg = `
                <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="${size/2}" cy="${size/2}" r="${size/2 - 2}" fill="${color}" stroke="white" stroke-width="2" opacity="0.9"/>
                    <text x="${size/2}" y="${size/2 + 5}" font-family="Arial" font-size="14" font-weight="bold" fill="white" text-anchor="middle">${label}</text>
                </svg>
            `;
            const iconUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
            return new AMap.Icon({
                image: iconUrl,
                size: new AMap.Size(size, size),
                imageSize: new AMap.Size(size, size)
            });
        }
        
        // 为每个商圈创建标记和信息窗口
        clusters.forEach((cluster, clusterIdx) => {
            const color = colors[clusterIdx % colors.length];
            const clusterGroup = {
                markers: [],
                polyline: null,
                infoDiv: null,
                clusterId: cluster.cluster_id
            };
            
            // 创建该商圈的所有标记
            cluster.markers.forEach((markerData, markerIdx) => {
                const label = markerIdx + 1;
                const marker = new AMap.Marker({
                    position: [markerData.lon, markerData.lat],
                    title: markerData.name,
                    icon: createCustomIcon(color, label),
                    zIndex: 100 + clusterIdx
                });
                
                const infoWindow = new AMap.InfoWindow({
                    content: `
                        <div style="padding: 10px; min-width: 200px;">
                            <h3 style="margin: 0 0 10px 0; color: ${color}; border-bottom: 2px solid ${color}; padding-bottom: 5px;">${markerData.name}</h3>
                            <p style="margin: 5px 0;"><strong>品牌:</strong> <span style="color: ${color}; font-weight: bold;">${markerData.brand}</span></p>
                            <p style="margin: 5px 0;"><strong>地址:</strong> ${markerData.address}</p>
                            <p style="margin: 5px 0; color: #666; font-size: 12px;">商圈 #${cluster.cluster_id} - 门店 ${label}/${cluster.markers.length}</p>
                        </div>
                    `,
                    offset: new AMap.Pixel(0, -30)
                });
                
                marker.on('click', function() {
                    infoWindow.open(map, marker.getPosition());
                    // 高亮显示该商圈
                    highlightCluster(clusterIdx);
                });
                
                map.add(marker);
                clusterGroup.markers.push(marker);
            });
            
            // 如果商圈有多个门店，绘制连接线
            if (cluster.markers.length > 1) {
                const path = cluster.markers.map(m => [m.lon, m.lat]);
                const polyline = new AMap.Polyline({
                    path: path,
                    strokeColor: color,
                    strokeWeight: 4,
                    strokeOpacity: 0.7,
                    strokeStyle: 'solid',
                    zIndex: 10 + clusterIdx
                });
                map.add(polyline);
                clusterGroup.polyline = polyline;
            }
            
            // 添加商圈信息到侧边栏
            const clusterDiv = document.createElement('div');
            clusterDiv.className = 'cluster-info';
            clusterDiv.dataset.clusterIndex = clusterIdx;
            clusterDiv.innerHTML = `
                <h3 style="color: ${color}; border-left: 4px solid ${color}; padding-left: 8px;">商圈 #${cluster.cluster_id}</h3>
                <p style="margin: 5px 0; font-size: 13px;"><strong>品牌数:</strong> ${cluster.brand_count}</p>
                <p style="margin: 5px 0; font-size: 13px;"><strong>最大距离:</strong> ${cluster.max_distance.toFixed(2)} 米</p>
                <div style="margin-top: 10px;">
                    ${cluster.markers.map((m, idx) => `
                        <div class="store-item">
                            <span class="store-brand">[${m.brand}]</span> ${m.name}
                        </div>
                    `).join('')}
                </div>
            `;
            
            // 点击侧边栏卡片时，跳转到地图并高亮
            clusterDiv.addEventListener('click', function() {
                highlightCluster(clusterIdx);
                // 计算商圈中心点
                const lats = cluster.markers.map(m => m.lat);
                const lons = cluster.markers.map(m => m.lon);
                const centerLat = lats.reduce((a, b) => a + b) / lats.length;
                const centerLon = lons.reduce((a, b) => a + b) / lons.length;
                
                // 跳转到商圈位置
                map.setZoomAndCenter(15, [centerLon, centerLat]);
                
                // 打开第一个标记的信息窗口
                if (clusterGroup.markers.length > 0) {
                    const firstMarker = clusterGroup.markers[0];
                    const markerData = cluster.markers[0];
                    const infoWindow = new AMap.InfoWindow({
                        content: `
                            <div style="padding: 10px; min-width: 200px;">
                                <h3 style="margin: 0 0 10px 0; color: ${color}; border-bottom: 2px solid ${color}; padding-bottom: 5px;">${markerData.name}</h3>
                                <p style="margin: 5px 0;"><strong>品牌:</strong> <span style="color: ${color}; font-weight: bold;">${markerData.brand}</span></p>
                                <p style="margin: 5px 0;"><strong>地址:</strong> ${markerData.address}</p>
                                <p style="margin: 5px 0; color: #666; font-size: 12px;">商圈 #${cluster.cluster_id}</p>
                            </div>
                        `,
                        offset: new AMap.Pixel(0, -30)
                    });
                    infoWindow.open(map, firstMarker.getPosition());
                }
            });
            
            document.getElementById('clusterList').appendChild(clusterDiv);
            clusterGroup.infoDiv = clusterDiv;
            clusterGroups.push(clusterGroup);
        });
        
        // 高亮显示指定商圈
        function highlightCluster(clusterIdx) {
            // 移除所有高亮
            document.querySelectorAll('.cluster-info').forEach(div => {
                div.classList.remove('active');
            });
            
            // 高亮选中的商圈
            if (clusterGroups[clusterIdx] && clusterGroups[clusterIdx].infoDiv) {
                clusterGroups[clusterIdx].infoDiv.classList.add('active');
                // 滚动到可见区域
                clusterGroups[clusterIdx].infoDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        
        // 调整地图视野以包含所有标记
        if (clusters.length > 0) {
            const allPoints = [];
            clusters.forEach(cluster => {
                cluster.markers.forEach(m => {
                    allPoints.push([m.lon, m.lat]);
                });
            });
            map.setFitView(null, false, [100, 100, 100, 100]);
        }
    </script>
</body>
</html>"""
    
    return html_content

