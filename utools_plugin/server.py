#!/usr/bin/env python3
"""
uTools 插件后端服务
使用 Flask 提供 API 接口
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amap_api import search_brands
from cluster_finder import find_clusters
from output import output_html
import tempfile
import webbrowser

app = Flask(__name__)
CORS(app)  # 允许跨域请求


@app.route('/api/find_clusters', methods=['POST'])
def api_find_clusters():
    """查找商圈 API"""
    try:
        data = request.json
        city = data.get('city')
        brands = data.get('brands', [])
        threshold = float(data.get('threshold', 200))
        api_key = data.get('api_key')
        
        if not city or not brands:
            return jsonify({'error': '缺少必要参数'}), 400
        
        if not api_key:
            return jsonify({'error': '缺少API密钥'}), 400
        
        # 设置 API 密钥（临时）
        import config
        config.AMAP_API_KEY = api_key
        
        # 搜索品牌门店
        brand_stores = search_brands(city, brands)
        
        # 过滤掉没有门店的品牌
        brands_with_stores = [b for b in brands if brand_stores.get(b)]
        if not brands_with_stores:
            return jsonify({
                'clusters': [],
                'message': '未找到任何品牌的门店'
            })
        
        # 查找商圈
        clusters = find_clusters(
            {brand: brand_stores[brand] for brand in brands_with_stores},
            threshold
        )
        
        # 生成 HTML 地图
        html_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.html', 
            delete=False,
            encoding='utf-8'
        )
        output_html(clusters, city, html_file.name)
        html_file.close()
        
        return jsonify({
            'clusters': clusters,
            'html_file': html_file.name,
            'cluster_count': len(clusters)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/open_html', methods=['POST'])
def api_open_html():
    """打开 HTML 文件"""
    try:
        data = request.json
        html_file = data.get('html_file')
        
        if html_file and os.path.exists(html_file):
            webbrowser.open(f'file://{os.path.abspath(html_file)}')
            return jsonify({'success': True})
        else:
            return jsonify({'error': '文件不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('启动 uTools 插件后端服务...')
    print('服务地址: http://localhost:8765')
    app.run(host='127.0.0.1', port=8765, debug=False)

