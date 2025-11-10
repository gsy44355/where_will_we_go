#!/usr/bin/env python3
"""
Flask Web应用主文件
"""
import os
import json
import time
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, stream_with_context
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from amap_api import search_brands_with_progress
from cluster_finder import find_clusters
from output import output_html_string
from config import DEFAULT_DISTANCE_THRESHOLD, AMAP_API_KEY
from log_capture import LogCapture

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


@app.route('/api/search/stream', methods=['POST'])
@login_required
def api_search_stream():
    """API接口：执行商圈搜索（流式响应，支持进度显示）"""
    def generate():
        try:
            data = request.get_json()
            city = data.get('city', '').strip()
            brands_str = data.get('brands', '').strip()
            threshold = float(data.get('threshold', DEFAULT_DISTANCE_THRESHOLD))
            
            # 验证输入
            if not city:
                yield f"data: {json.dumps({'type': 'error', 'message': '请输入城市名称'})}\n\n"
                return
            
            if not brands_str:
                yield f"data: {json.dumps({'type': 'error', 'message': '请输入品牌列表'})}\n\n"
                return
            
            # 检查API密钥
            if not AMAP_API_KEY or AMAP_API_KEY == "your_api_key_here":
                yield f"data: {json.dumps({'type': 'error', 'message': '高德地图API密钥未配置'})}\n\n"
                return
            
            # 解析品牌列表
            brands = [b.strip() for b in brands_str.split(",") if b.strip()]
            if not brands:
                yield f"data: {json.dumps({'type': 'error', 'message': '请至少提供一个品牌名称'})}\n\n"
                return
            
            # 发送开始搜索消息
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'searching', 'message': f'开始搜索 {len(brands)} 个品牌的门店...', 'progress': 0})}\n\n"
            
            # 搜索各品牌的门店（带进度回调）
            brand_stores = {}
            progress_messages = []
            log_queue = queue.Queue()
            searched_brands = 0
            total_brands = len(brands)
            search_done = threading.Event()
            search_error = [None]
            
            def progress_callback(brand, current, total, message):
                nonlocal searched_brands
                searched_brands = current
                progress_messages.append({
                    'type': 'progress',
                    'stage': 'searching',
                    'brand': brand,
                    'current': current,
                    'total': total,
                    'message': message,
                    'progress': int((current / total) * 40)  # 搜索阶段占40%
                })
                # 实时发送进度消息
                log_queue.put(('progress', progress_messages[-1]))
            
            def log_callback(message: str):
                """捕获日志输出并实时发送"""
                log_queue.put(('log', {'type': 'log', 'message': message, 'stage': 'searching'}))
            
            def do_search():
                """在单独线程中执行搜索"""
                try:
                    nonlocal brand_stores
                    with LogCapture(log_callback):
                        brand_stores = search_brands_with_progress(city, brands, progress_callback)
                except Exception as e:
                    search_error[0] = e
                finally:
                    search_done.set()
            
            try:
                # 启动搜索线程
                search_thread = threading.Thread(target=do_search)
                search_thread.start()
                
                # 实时发送日志和进度消息
                while not search_done.is_set() or not log_queue.empty():
                    try:
                        msg_type, msg_data = log_queue.get(timeout=0.1)
                        if msg_type == 'log':
                            yield f"data: {json.dumps(msg_data)}\n\n"
                        elif msg_type == 'progress':
                            yield f"data: {json.dumps(msg_data)}\n\n"
                    except queue.Empty:
                        continue
                
                # 等待搜索线程完成
                search_thread.join()
                
                # 发送剩余的日志和进度消息
                while not log_queue.empty():
                    try:
                        msg_type, msg_data = log_queue.get_nowait()
                        yield f"data: {json.dumps(msg_data)}\n\n"
                    except queue.Empty:
                        break
                
                if search_error[0]:
                    raise search_error[0]
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'搜索门店时出错: {str(e)}'})}\n\n"
                return
            
            # 检查是否有品牌没有找到门店
            brands_with_stores = [b for b in brands if brand_stores.get(b)]
            if not brands_with_stores:
                yield f"data: {json.dumps({'type': 'error', 'message': '未找到任何品牌的门店'})}\n\n"
                return
            
            if len(brands_with_stores) < len(brands):
                missing_brands = set(brands) - set(brands_with_stores)
                yield f"data: {json.dumps({'type': 'progress', 'stage': 'searching', 'message': f'警告: 以下品牌未找到门店: {", ".join(missing_brands)}', 'progress': 40})}\n\n"
            
            # 发送开始查找商圈消息
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'clustering', 'message': '正在查找符合条件的商圈...', 'progress': 40})}\n\n"
            
            # 查找商圈（捕获日志输出）
            log_queue_clustering = queue.Queue()
            clustering_progress_updates = []
            clustering_done = threading.Event()
            clustering_error = [None]
            clusters_result = [None]
            
            def log_callback_clustering(message: str):
                """捕获商圈查找过程中的日志输出并实时发送"""
                log_queue_clustering.put(('log', {'type': 'log', 'message': message, 'stage': 'clustering'}))
                # 根据日志内容更新进度
                if '构建空间索引' in message:
                    log_queue_clustering.put(('progress', {'type': 'progress', 'stage': 'clustering', 'message': message, 'progress': 45}))
                elif '构建候选集' in message:
                    log_queue_clustering.put(('progress', {'type': 'progress', 'stage': 'clustering', 'message': message, 'progress': 50}))
                elif '查找商圈' in message or '查找商圈:' in message:
                    log_queue_clustering.put(('progress', {'type': 'progress', 'stage': 'clustering', 'message': message, 'progress': 60}))
                elif '原始组合数' in message:
                    log_queue_clustering.put(('progress', {'type': 'progress', 'stage': 'clustering', 'message': message, 'progress': 55}))
                elif '优化后组合数' in message:
                    log_queue_clustering.put(('progress', {'type': 'progress', 'stage': 'clustering', 'message': message, 'progress': 65}))
            
            def do_clustering():
                """在单独线程中执行商圈查找"""
                try:
                    with LogCapture(log_callback_clustering):
                        clusters_result[0] = find_clusters(
                            {brand: brand_stores[brand] for brand in brands_with_stores},
                            threshold
                        )
                except Exception as e:
                    clustering_error[0] = e
                finally:
                    clustering_done.set()
            
            try:
                # 启动商圈查找线程
                clustering_thread = threading.Thread(target=do_clustering)
                clustering_thread.start()
                
                # 实时发送日志和进度消息
                while not clustering_done.is_set() or not log_queue_clustering.empty():
                    try:
                        msg_type, msg_data = log_queue_clustering.get(timeout=0.1)
                        yield f"data: {json.dumps(msg_data)}\n\n"
                    except queue.Empty:
                        continue
                
                # 等待商圈查找线程完成
                clustering_thread.join()
                
                # 发送剩余的日志
                while not log_queue_clustering.empty():
                    try:
                        msg_type, msg_data = log_queue_clustering.get_nowait()
                        yield f"data: {json.dumps(msg_data)}\n\n"
                    except queue.Empty:
                        break
                
                if clustering_error[0]:
                    raise clustering_error[0]
                
                clusters = clusters_result[0]
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'查找商圈时出错: {str(e)}'})}\n\n"
                return
            
            if not clusters:
                yield f"data: {json.dumps({'type': 'error', 'message': '未找到符合条件的商圈', 'brands_found': brands_with_stores})}\n\n"
                return
            
            # 发送找到商圈的消息
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'clustering', 'message': f'找到 {len(clusters)} 个符合条件的商圈', 'progress': 80})}\n\n"
            
            # 发送生成结果消息
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'generating', 'message': '正在生成结果...', 'progress': 85})}\n\n"
            
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
            
            # 发送完成消息
            yield f"data: {json.dumps({'type': 'complete', 'result': result, 'html_content': html_content, 'progress': 100})}\n\n"
            
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'参数错误: {str(e)}'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'服务器错误: {str(e)}'})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


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

