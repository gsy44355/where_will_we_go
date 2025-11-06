// 高德地图 API 封装 - JavaScript 版本
async function searchPOI(apiKey, city, keyword, maxPages = 10) {
    const stores = [];
    let page = 1;
    
    while (page <= maxPages) {
        try {
            const url = `https://restapi.amap.com/v3/place/text`;
            const params = new URLSearchParams({
                key: apiKey,
                keywords: keyword,
                city: city,
                offset: '20',
                page: page.toString(),
                extensions: 'all'
            });
            
            const response = await fetch(`${url}?${params}`);
            const data = await response.json();
            
            if (data.status !== '1') {
                const errorMsg = data.info || '未知错误';
                console.warn(`搜索 ${keyword} 时出错 - ${errorMsg}`);
                break;
            }
            
            const pois = data.pois || [];
            if (pois.length === 0) {
                break;
            }
            
            for (const poi of pois) {
                const location = poi.location ? poi.location.split(',') : [];
                if (location.length === 2) {
                    stores.push({
                        name: poi.name || '',
                        address: poi.address || '',
                        lat: parseFloat(location[1]),
                        lon: parseFloat(location[0]),
                        poi_id: poi.id || '',
                        type: poi.type || ''
                    });
                }
            }
            
            const count = parseInt(data.count || 0);
            if (stores.length >= count || pois.length < 20) {
                break;
            }
            
            page++;
            // 避免请求过快
            await new Promise(resolve => setTimeout(resolve, 100));
            
        } catch (error) {
            console.error(`请求高德地图API失败 - ${error.message}`);
            break;
        }
    }
    
    return stores;
}

async function searchBrands(apiKey, city, brands) {
    const brandStores = {};
    
    for (const brand of brands) {
        const stores = await searchPOI(apiKey, city, brand);
        if (stores.length > 0) {
            brandStores[brand] = stores;
        } else {
            console.warn(`未找到 ${brand} 在 ${city} 的门店`);
            brandStores[brand] = [];
        }
        // 品牌之间延迟
        await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    return brandStores;
}

