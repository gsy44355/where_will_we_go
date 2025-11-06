// 商圈查找算法 - JavaScript 版本（简化版，使用空间索引优化）
class SpatialGrid {
    constructor(stores, threshold) {
        this.threshold = threshold;
        this.gridSize = threshold * 2;
        this.grid = new Map();
        this.stores = stores;
        
        for (let idx = 0; idx < stores.length; idx++) {
            const gridKey = this.getGridKey(stores[idx].lat, stores[idx].lon);
            if (!this.grid.has(gridKey)) {
                this.grid.set(gridKey, []);
            }
            this.grid.get(gridKey).push(idx);
        }
    }
    
    getGridKey(lat, lon) {
        const gridLat = Math.floor(lat / (this.gridSize / 111000));
        const gridLon = Math.floor(lon / (this.gridSize / (111000 * Math.cos(lat * Math.PI / 180))));
        return `${gridLat},${gridLon}`;
    }
    
    getNearbyStores(storeIdx) {
        const store = this.stores[storeIdx];
        const gridKey = this.getGridKey(store.lat, store.lon);
        const [gridLat, gridLon] = gridKey.split(',').map(Number);
        
        const nearby = new Set();
        
        for (let dlat = -1; dlat <= 1; dlat++) {
            for (let dlon = -1; dlon <= 1; dlon++) {
                const checkKey = `${gridLat + dlat},${gridLon + dlon}`;
                const storesInGrid = this.grid.get(checkKey) || [];
                
                for (const otherIdx of storesInGrid) {
                    if (otherIdx !== storeIdx) {
                        const otherStore = this.stores[otherIdx];
                        const dist = haversineDistance(
                            store.lat, store.lon,
                            otherStore.lat, otherStore.lon
                        );
                        if (dist <= this.threshold) {
                            nearby.add(otherIdx);
                        }
                    }
                }
            }
        }
        
        return nearby;
    }
}

async function findClusters(brandStoresDict, threshold) {
    const brands = Object.keys(brandStoresDict).filter(b => brandStoresDict[b].length > 0);
    
    if (brands.length === 0) {
        return [];
    }
    
    if (brands.length === 1) {
        const brand = brands[0];
        return brandStoresDict[brand].map(store => ({
            brands: { [brand]: store },
            stores: [store],
            max_distance: 0,
            brand_count: 1
        }));
    }
    
    // 构建所有门店的索引映射
    const allStores = [];
    const brandToIndices = {};
    const storeToBrand = {};
    
    for (const brand of brands) {
        const brandIndices = [];
        for (const store of brandStoresDict[brand]) {
            const idx = allStores.length;
            allStores.push(store);
            brandIndices.push(idx);
            storeToBrand[idx] = brand;
        }
        brandToIndices[brand] = brandIndices;
    }
    
    // 构建空间索引
    console.log('构建空间索引...');
    const spatialGrid = new SpatialGrid(allStores, threshold);
    
    // 构建候选集
    console.log('构建候选集...');
    const brandCandidates = {};
    
    for (const brand of brands) {
        brandCandidates[brand] = {};
        for (const storeIdx of brandToIndices[brand]) {
            const nearby = spatialGrid.getNearbyStores(storeIdx);
            const candidatesByBrand = {};
            
            for (const otherIdx of nearby) {
                const otherBrand = storeToBrand[otherIdx];
                if (otherBrand !== brand) {
                    if (!candidatesByBrand[otherBrand]) {
                        candidatesByBrand[otherBrand] = [];
                    }
                    candidatesByBrand[otherBrand].push(otherIdx);
                }
            }
            
            brandCandidates[brand][storeIdx] = candidatesByBrand;
        }
    }
    
    // 查找商圈
    console.log('查找商圈...');
    const validClusters = [];
    const firstBrand = brands[0];
    
    // 生成所有组合的函数
    function product(...arrays) {
        if (arrays.length === 0) {
            return [[]];
        }
        const [first, ...rest] = arrays;
        const result = [];
        for (const item of first) {
            const restProducts = product(...rest);
            for (const combination of restProducts) {
                result.push([item, ...combination]);
            }
        }
        return result;
    }
    
    for (const firstStoreIdx of brandToIndices[firstBrand]) {
        const candidates = brandCandidates[firstBrand][firstStoreIdx];
        
        if (!brands.slice(1).every(brand => brand in candidates && candidates[brand].length > 0)) {
            continue;
        }
        
        const candidateLists = brands.slice(1).map(brand => candidates[brand]);
        
        for (const combination of product(...candidateLists)) {
            const storeIndices = [firstStoreIdx, ...combination];
            const stores = storeIndices.map(idx => allStores[idx]);
            
            const { valid, maxDistance } = checkAllDistances(stores, threshold);
            
            if (valid) {
                const brandsDict = {};
                for (const idx of storeIndices) {
                    const brand = storeToBrand[idx];
                    brandsDict[brand] = allStores[idx];
                }
                
                validClusters.push({
                    brands: brandsDict,
                    stores: stores,
                    max_distance: maxDistance,
                    brand_count: brands.length
                });
            }
        }
    }
    
    if (validClusters.length > 0) {
        return validClusters;
    }
    
    // 如果没有完全符合条件的，尝试部分品牌组合
    console.log('未找到完全符合条件的商圈，尝试部分品牌组合...');
    
    // 组合生成函数
    function combinations(arr, r) {
        if (r === 0) {
            return [[]];
        }
        if (r > arr.length) {
            return [];
        }
        const result = [];
        for (let i = 0; i <= arr.length - r; i++) {
            const restCombos = combinations(arr.slice(i + 1), r - 1);
            for (const combo of restCombos) {
                result.push([arr[i], ...combo]);
            }
        }
        return result;
    }
    
    const allPartialClusters = [];
    
    for (let r = brands.length - 1; r >= 2; r--) {
        const brandSubsets = combinations(brands, r);
        for (const brandSubset of brandSubsets) {
            const firstBrandSub = brandSubset[0];
            
            for (const firstStoreIdx of brandToIndices[firstBrandSub]) {
                const candidates = brandCandidates[firstBrandSub][firstStoreIdx];
                
                if (!brandSubset.slice(1).every(brand => brand in candidates && candidates[brand].length > 0)) {
                    continue;
                }
                
                const candidateLists = brandSubset.slice(1).map(brand => candidates[brand]);
                
                for (const combination of product(...candidateLists)) {
                    const storeIndices = [firstStoreIdx, ...combination];
                    const stores = storeIndices.map(idx => allStores[idx]);
                    
                    const { valid, maxDistance } = checkAllDistances(stores, threshold);
                    
                    if (valid) {
                        const brandsDict = {};
                        for (const idx of storeIndices) {
                            const brand = storeToBrand[idx];
                            brandsDict[brand] = allStores[idx];
                        }
                        
                        allPartialClusters.push({
                            brands: brandsDict,
                            stores: stores,
                            max_distance: maxDistance,
                            brand_count: brandSubset.length
                        });
                    }
                }
            }
        }
        
        if (allPartialClusters.length > 0) {
            break; // 找到后停止
        }
    }
    
    if (allPartialClusters.length > 0) {
        allPartialClusters.sort((a, b) => b.brand_count - a.brand_count);
        return allPartialClusters;
    }
    
    return [];
}

