// HTML 地图生成 - JavaScript 版本
function generateMapHTML(clusters, city, apiKey) {
    // 生成标记点数据
    const markersData = [];
    clusters.forEach((cluster, idx) => {
        const clusterMarkers = [];
        Object.entries(cluster.brands).forEach(([brand, store]) => {
            clusterMarkers.push({
                name: store.name,
                address: store.address,
                lat: store.lat,
                lon: store.lon,
                brand: brand
            });
        });
        markersData.push({
            cluster_id: idx + 1,
            max_distance: cluster.max_distance,
            brand_count: cluster.brand_count || Object.keys(cluster.brands).length,
            markers: clusterMarkers
        });
    });
    
    // 计算地图中心点
    let centerLat = 39.9042; // 北京默认坐标
    let centerLon = 116.4074;
    
    if (clusters.length > 0) {
        const allLats = [];
        const allLons = [];
        clusters.forEach(cluster => {
            cluster.stores.forEach(store => {
                allLats.push(store.lat);
                allLons.push(store.lon);
            });
        });
        centerLat = allLats.reduce((a, b) => a + b) / allLats.length;
        centerLon = allLons.reduce((a, b) => a + b) / allLons.length;
    }
    
    const clustersJson = JSON.stringify(markersData);
    
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>商圈地图 - ${city}</title>
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
        <p>城市: ${city}</p>
        <p>找到 ${clusters.length} 个商圈</p>
        <div id="clusterList"></div>
    </div>
    
    <script src="https://webapi.amap.com/maps?v=2.0&key=${apiKey}"></script>
    <script>
        const clusters = ${clustersJson};
        const center = [${centerLon}, ${centerLat}];
        
        const map = new AMap.Map('mapContainer', {
            zoom: 13,
            center: center,
            mapStyle: 'amap://styles/normal'
        });
        
        const colors = ['#FF4444', '#44AA44', '#4444FF', '#FFAA00', '#AA44FF', '#00AAAA', '#FF8800', '#8844AA'];
        const clusterGroups = [];
        
        function createCustomIcon(color, label) {
            const size = 40;
            const svg = \`<svg width="\${size}" height="\${size}" xmlns="http://www.w3.org/2000/svg"><circle cx="\${size/2}" cy="\${size/2}" r="\${size/2 - 2}" fill="\${color}" stroke="white" stroke-width="2" opacity="0.9"/><text x="\${size/2}" y="\${size/2 + 5}" font-family="Arial" font-size="14" font-weight="bold" fill="white" text-anchor="middle">\${label}</text></svg>\`;
            const iconUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
            return new AMap.Icon({
                image: iconUrl,
                size: new AMap.Size(size, size),
                imageSize: new AMap.Size(size, size)
            });
        }
        
        clusters.forEach((cluster, clusterIdx) => {
            const color = colors[clusterIdx % colors.length];
            const clusterGroup = {
                markers: [],
                polyline: null,
                infoDiv: null,
                clusterId: cluster.cluster_id
            };
            
            cluster.markers.forEach((markerData, markerIdx) => {
                const label = markerIdx + 1;
                const marker = new AMap.Marker({
                    position: [markerData.lon, markerData.lat],
                    title: markerData.name,
                    icon: createCustomIcon(color, label),
                    zIndex: 100 + clusterIdx
                });
                
                const infoWindow = new AMap.InfoWindow({
                    content: \`<div style="padding: 10px; min-width: 200px;"><h3 style="margin: 0 0 10px 0; color: \${color}; border-bottom: 2px solid \${color}; padding-bottom: 5px;">\${markerData.name}</h3><p style="margin: 5px 0;"><strong>品牌:</strong> <span style="color: \${color}; font-weight: bold;">\${markerData.brand}</span></p><p style="margin: 5px 0;"><strong>地址:</strong> \${markerData.address}</p><p style="margin: 5px 0; color: #666; font-size: 12px;">商圈 #\${cluster.cluster_id} - 门店 \${label}/\${cluster.markers.length}</p></div>\`,
                    offset: new AMap.Pixel(0, -30)
                });
                
                marker.on('click', function() {
                    infoWindow.open(map, marker.getPosition());
                    highlightCluster(clusterIdx);
                });
                
                map.add(marker);
                clusterGroup.markers.push(marker);
            });
            
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
            
            const clusterDiv = document.createElement('div');
            clusterDiv.className = 'cluster-info';
            clusterDiv.dataset.clusterIndex = clusterIdx;
            clusterDiv.innerHTML = \`<h3 style="color: \${color}; border-left: 4px solid \${color}; padding-left: 8px;">商圈 #\${cluster.cluster_id}</h3><p style="margin: 5px 0; font-size: 13px;"><strong>品牌数:</strong> \${cluster.brand_count}</p><p style="margin: 5px 0; font-size: 13px;"><strong>最大距离:</strong> \${cluster.max_distance.toFixed(2)} 米</p><div style="margin-top: 10px;">\${cluster.markers.map((m, idx) => \`<div class="store-item"><span class="store-brand">[\${m.brand}]</span> \${m.name}</div>\`).join('')}</div>\`;
            
            clusterDiv.addEventListener('click', function() {
                highlightCluster(clusterIdx);
                const lats = cluster.markers.map(m => m.lat);
                const lons = cluster.markers.map(m => m.lon);
                const centerLat = lats.reduce((a, b) => a + b) / lats.length;
                const centerLon = lons.reduce((a, b) => a + b) / lons.length;
                map.setZoomAndCenter(15, [centerLon, centerLat]);
                
                if (clusterGroup.markers.length > 0) {
                    const firstMarker = clusterGroup.markers[0];
                    const markerData = cluster.markers[0];
                    const infoWindow = new AMap.InfoWindow({
                        content: \`<div style="padding: 10px; min-width: 200px;"><h3 style="margin: 0 0 10px 0; color: \${color}; border-bottom: 2px solid \${color}; padding-bottom: 5px;">\${markerData.name}</h3><p style="margin: 5px 0;"><strong>品牌:</strong> <span style="color: \${color}; font-weight: bold;">\${markerData.brand}</span></p><p style="margin: 5px 0;"><strong>地址:</strong> \${markerData.address}</p><p style="margin: 5px 0; color: #666; font-size: 12px;">商圈 #\${cluster.cluster_id}</p></div>\`,
                        offset: new AMap.Pixel(0, -30)
                    });
                    infoWindow.open(map, firstMarker.getPosition());
                }
            });
            
            document.getElementById('clusterList').appendChild(clusterDiv);
            clusterGroup.infoDiv = clusterDiv;
            clusterGroups.push(clusterGroup);
        });
        
        function highlightCluster(clusterIdx) {
            document.querySelectorAll('.cluster-info').forEach(div => {
                div.classList.remove('active');
            });
            if (clusterGroups[clusterIdx] && clusterGroups[clusterIdx].infoDiv) {
                clusterGroups[clusterIdx].infoDiv.classList.add('active');
                clusterGroups[clusterIdx].infoDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        
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
</html>`;
}

function openMapInNewWindow(htmlContent) {
    try {
        // 优先方法：如果 uTools 提供了文件保存功能，使用它
        if (window.saveAndOpenHTML && typeof window.saveAndOpenHTML === 'function') {
            try {
                const success = window.saveAndOpenHTML(htmlContent, `商圈地图_${Date.now()}.html`);
                if (success) {
                    return true;
                }
            } catch (e) {
                console.log('使用 Node.js 保存文件失败，尝试其他方法:', e);
            }
        }
        
        // 方法1: 使用 data URL（最兼容的方式）
        const dataUrl = 'data:text/html;charset=utf-8,' + encodeURIComponent(htmlContent);
        
        // 在 uTools 环境中，尝试使用 shellOpenPath
        if (window.utools && typeof window.utools.shellOpenPath === 'function') {
            try {
                // uTools 的 shellOpenPath 可以打开 URL
                window.utools.shellOpenPath(dataUrl);
                return true;
            } catch (e) {
                console.log('shellOpenPath 失败，尝试其他方法:', e);
            }
        }
        
        // 方法2: 使用 window.open 打开 data URL
        const newWindow = window.open(dataUrl, '_blank');
        if (newWindow && !newWindow.closed) {
            // 检查窗口是否真的打开了
            setTimeout(() => {
                if (newWindow.closed) {
                    console.log('窗口被关闭');
                }
            }, 100);
            return true;
        }
        
        // 方法3: 使用 Blob URL
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const blobUrl = URL.createObjectURL(blob);
        const blobWindow = window.open(blobUrl, '_blank', 'width=1200,height=800');
        
        if (blobWindow && !blobWindow.closed) {
            // 成功打开，延迟清理 URL
            setTimeout(() => {
                URL.revokeObjectURL(blobUrl);
            }, 1000);
            return true;
        }
        
        // 方法4: 使用 document.write（降级方案）
        try {
            const writeWindow = window.open('', '_blank', 'width=1200,height=800');
            if (writeWindow) {
                writeWindow.document.write(htmlContent);
                writeWindow.document.close();
                URL.revokeObjectURL(blobUrl);
                return true;
            }
        } catch (e) {
            console.error('使用 document.write 失败:', e);
        }
        
        URL.revokeObjectURL(blobUrl);
        return false;
        
    } catch (error) {
        console.error('打开窗口失败:', error);
        return false;
    }
}

// 下载 HTML 文件（用于降级方案）
function downloadHTML(htmlContent, filename) {
    try {
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => {
            URL.revokeObjectURL(url);
        }, 100);
        return true;
    } catch (error) {
        console.error('下载文件失败:', error);
        return false;
    }
}

