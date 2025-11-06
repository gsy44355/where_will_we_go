// 距离计算模块 - JavaScript 版本
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // 地球半径（米）
    
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const deltaPhi = (lat2 - lat1) * Math.PI / 180;
    const deltaLambda = (lon2 - lon1) * Math.PI / 180;
    
    const a = Math.sin(deltaPhi / 2) ** 2 +
        Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    
    return R * c;
}

function checkAllDistances(stores, threshold) {
    if (stores.length < 2) {
        return { valid: true, maxDistance: 0 };
    }
    
    let maxDistance = 0;
    
    for (let i = 0; i < stores.length; i++) {
        for (let j = i + 1; j < stores.length; j++) {
            const distance = haversineDistance(
                stores[i].lat, stores[i].lon,
                stores[j].lat, stores[j].lon
            );
            maxDistance = Math.max(maxDistance, distance);
            
            if (distance > threshold) {
                return { valid: false, maxDistance };
            }
        }
    }
    
    return { valid: true, maxDistance };
}

