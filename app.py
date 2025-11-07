#!/usr/bin/env python3
"""
Flask Web应用主文件
"""
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from amap_api import search_brands
from cluster_finder import find_clusters
from output import output_html_string
from config import DEFAULT_DISTANCE_THRESHOLD, AMAP_API_KEY

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# 从环境变量读取登录凭据（默认用户名和密码）
DEFAULT_USERNAME = os.getenv('WEB_USERNAME', 'admin')
DEFAULT_PASSWORD_HASH = generate_password_hash(os.getenv('WEB_PASSWORD', 'admin123'))

# 存储用户会话中的搜索结果
app.config['RESULTS_DIR'] = os.path.join(os.path.dirname(__file__), 'results')


def login_required(f):
    """登录装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """首页，重定向到登录或搜索页"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('search'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # 验证用户名和密码
        if username == DEFAULT_USERNAME and check_password_hash(DEFAULT_PASSWORD_HASH, password):
            session['user_id'] = username
            session['login_time'] = datetime.now().isoformat()
            return jsonify({'success': True, 'redirect': url_for('search')})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    
    # GET请求，显示登录页面
    if 'user_id' in session:
        return redirect(url_for('search'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/search')
@login_required
def search():
    """搜索页面"""
    return render_template('search.html')


@app.route('/api/search', methods=['POST'])
@login_required
def api_search():
    """API接口：执行商圈搜索"""
    try:
        data = request.get_json()
        city = data.get('city', '').strip()
        brands_str = data.get('brands', '').strip()
        threshold = float(data.get('threshold', DEFAULT_DISTANCE_THRESHOLD))
        
        # 验证输入
        if not city:
            return jsonify({'success': False, 'message': '请输入城市名称'}), 400
        
        if not brands_str:
            return jsonify({'success': False, 'message': '请输入品牌列表'}), 400
        
        # 检查API密钥
        if not AMAP_API_KEY or AMAP_API_KEY == "your_api_key_here":
            return jsonify({'success': False, 'message': '高德地图API密钥未配置'}), 500
        
        # 解析品牌列表
        brands = [b.strip() for b in brands_str.split(",") if b.strip()]
        if not brands:
            return jsonify({'success': False, 'message': '请至少提供一个品牌名称'}), 400
        
        # 搜索各品牌的门店
        brand_stores = search_brands(city, brands)
        
        # 检查是否有品牌没有找到门店
        brands_with_stores = [b for b in brands if brand_stores.get(b)]
        if not brands_with_stores:
            return jsonify({'success': False, 'message': '未找到任何品牌的门店'}), 404
        
        # 查找商圈
        clusters = find_clusters(
            {brand: brand_stores[brand] for brand in brands_with_stores},
            threshold
        )
        
        if not clusters:
            return jsonify({
                'success': False,
                'message': '未找到符合条件的商圈',
                'brands_found': brands_with_stores
            }), 404
        
        # 生成结果
        result = {
            'success': True,
            'city': city,
            'brands': brands_with_stores,
            'threshold': threshold,
            'cluster_count': len(clusters),
            'clusters': clusters,
            'timestamp': datetime.now().isoformat()
        }
        
        # 生成HTML地图
        html_content = output_html_string(clusters, city)
        
        # 保存结果到session（用于后续查看）
        session['last_result'] = {
            'city': city,
            'brands': brands_with_stores,
            'cluster_count': len(clusters),
            'timestamp': result['timestamp']
        }
        
        return jsonify({
            'success': True,
            'result': result,
            'html_content': html_content
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': f'参数错误: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/result')
@login_required
def result():
    """结果展示页面"""
    return render_template('result.html')


@app.route('/map')
@login_required
def map_view():
    """地图查看页面（嵌入HTML）"""
    html_content = request.args.get('html', '')
    if not html_content:
        # 尝试从sessionStorage获取（通过JavaScript重定向）
        return render_template('map_view.html', html_content='')
    return render_template('map_view.html', html_content=html_content)


if __name__ == '__main__':
    # 确保结果目录存在
    os.makedirs(app.config['RESULTS_DIR'], exist_ok=True)
    
    # 运行应用
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

