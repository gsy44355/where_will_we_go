#!/usr/bin/env python3
"""
Flask Web应用主文件
"""
import os
import json
import threading
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, stream_with_context
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests as http_requests
from amap_api import search_brands_with_progress, search_brands
from cluster_finder import find_clusters
from output import output_html_string
from config import DEFAULT_DISTANCE_THRESHOLD, AMAP_API_KEY, AMAP_JS_KEY, AMAP_SECURITY_CODE
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


def _validate_search_params(data):
    """验证搜索参数，返回 (city, brands, threshold, required_brands) 或抛出 ValueError"""
    city = data.get('city', '').strip()
    brands_str = data.get('brands', '').strip()
    threshold = data.get('threshold', DEFAULT_DISTANCE_THRESHOLD)

    if not city:
        raise ValueError('请输入城市名称')
    if not brands_str:
        raise ValueError('请输入品牌列表')
    if not AMAP_API_KEY or AMAP_API_KEY == "your_api_key_here":
        raise ValueError('高德地图API密钥未配置')

    try:
        threshold = float(threshold)
    except (ValueError, TypeError):
        raise ValueError('距离阈值必须是数字')
    if threshold < 50 or threshold > 5000:
        raise ValueError('距离阈值应在 50-5000 米之间')

    brands = [b.strip() for b in brands_str.split(",") if b.strip()]
    if not brands:
        raise ValueError('请至少提供一个品牌名称')

    required_brands_str = data.get('required_brands', '').strip()
    required_brands = [b.strip() for b in required_brands_str.split(",") if b.strip()] if required_brands_str else None
    if required_brands:
        invalid = [b for b in required_brands if b not in brands]
        if invalid:
            raise ValueError(f'必选品牌必须是品牌列表的子集，以下不在列表中: {", ".join(invalid)}')

    return city, brands, threshold, required_brands


def _run_threaded_task(task_fn, msg_queue):
    """在线程中运行任务，yield 队列中的消息。通过 yield from 调用，返回 (result, error)。"""
    done = threading.Event()
    error_holder = [None]
    result_holder = [None]

    def worker():
        try:
            result_holder[0] = task_fn()
        except Exception as e:
            error_holder[0] = e
        finally:
            done.set()

    thread = threading.Thread(target=worker)
    thread.start()

    while not done.is_set() or not msg_queue.empty():
        try:
            msg = msg_queue.get(timeout=0.1)
            yield f"data: {json.dumps(msg)}\n\n"
        except queue.Empty:
            continue

    thread.join()

    while not msg_queue.empty():
        try:
            msg = msg_queue.get_nowait()
            yield f"data: {json.dumps(msg)}\n\n"
        except queue.Empty:
            break

    return result_holder[0], error_holder[0]


def _sse_msg(msg_type, message=None, **extra):
    """构造 SSE 消息字符串"""
    data = {'type': msg_type}
    if message is not None:
        data['message'] = message
    data.update(extra)
    return f"data: {json.dumps(data)}\n\n"


@app.errorhandler(403)
def handle_forbidden(e):
    """session 异常时清除 cookie 并跳转登录页"""
    session.clear()
    return redirect(url_for('login'))


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

        if username == DEFAULT_USERNAME and check_password_hash(DEFAULT_PASSWORD_HASH, password):
            session['user_id'] = username
            session['login_time'] = datetime.now().isoformat()
            return jsonify({'success': True, 'redirect': url_for('search')})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

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
    return render_template('search.html',
                           amap_js_key=AMAP_JS_KEY or AMAP_API_KEY)


@app.route('/api/search/stream', methods=['POST'])
@login_required
def api_search_stream():
    """API接口：执行商圈搜索（流式响应，支持进度显示）"""
    def generate():
        try:
            data = request.get_json()
            city, brands, threshold, required_brands = _validate_search_params(data)
        except (ValueError, Exception) as e:
            yield _sse_msg('error', str(e))
            return

        try:
            # --- 搜索阶段 ---
            yield _sse_msg('progress', f'开始搜索 {len(brands)} 个品牌的门店...',
                           stage='searching', progress=0)

            search_queue = queue.Queue()

            def progress_callback(brand, current, total, message):
                search_queue.put({
                    'type': 'progress', 'stage': 'searching',
                    'brand': brand, 'current': current, 'total': total,
                    'message': message, 'progress': int((current / total) * 40)
                })

            def search_log_cb(message):
                search_queue.put({'type': 'log', 'message': message, 'stage': 'searching'})

            def do_search():
                with LogCapture(search_log_cb):
                    return search_brands_with_progress(city, brands, progress_callback)

            brand_stores, error = yield from _run_threaded_task(do_search, search_queue)
            if error:
                yield _sse_msg('error', f'搜索门店时出错: {error}')
                return

            # 检查搜索结果
            brands_with_stores = [b for b in brands if brand_stores.get(b)]
            if not brands_with_stores:
                yield _sse_msg('error', '未找到任何品牌的门店')
                return

            if len(brands_with_stores) < len(brands):
                missing = set(brands) - set(brands_with_stores)
                yield _sse_msg('progress',
                               f'警告: 以下品牌未找到门店: {", ".join(missing)}',
                               stage='searching', progress=40)

            # --- 聚类阶段 ---
            yield _sse_msg('progress', '正在查找符合条件的商圈...',
                           stage='clustering', progress=40)

            cluster_queue = queue.Queue()
            _progress_keywords = {
                '构建空间索引': 45, '构建候选集': 50,
                '原始组合数': 55, '优化后组合数': 65,
            }

            def cluster_log_cb(message):
                cluster_queue.put({'type': 'log', 'message': message, 'stage': 'clustering'})
                for kw, prog in _progress_keywords.items():
                    if kw in message:
                        cluster_queue.put({'type': 'progress', 'stage': 'clustering',
                                           'message': message, 'progress': prog})
                        return
                if '查找商圈' in message:
                    cluster_queue.put({'type': 'progress', 'stage': 'clustering',
                                       'message': message, 'progress': 60})

            # 过滤掉未找到门店的必选品牌
            effective_required = [b for b in required_brands if b in brands_with_stores] if required_brands else None

            def do_clustering():
                with LogCapture(cluster_log_cb):
                    return find_clusters(
                        {b: brand_stores[b] for b in brands_with_stores},
                        threshold,
                        required_brands=effective_required
                    )

            clusters, error = yield from _run_threaded_task(do_clustering, cluster_queue)
            if error:
                yield _sse_msg('error', f'查找商圈时出错: {error}')
                return

            if not clusters:
                yield _sse_msg('error', '未找到符合条件的商圈')
                return

            # --- 生成结果 ---
            yield _sse_msg('progress', f'找到 {len(clusters)} 个符合条件的商圈',
                           stage='clustering', progress=80)
            yield _sse_msg('progress', '正在生成结果...',
                           stage='generating', progress=85)

            result = {
                'success': True, 'city': city, 'brands': brands_with_stores,
                'threshold': threshold, 'cluster_count': len(clusters),
                'clusters': clusters, 'timestamp': datetime.now().isoformat()
            }

            html_content = output_html_string(clusters, city, proxy_mode=True)

            session['last_result'] = {
                'city': city, 'brands': brands_with_stores,
                'cluster_count': len(clusters), 'timestamp': result['timestamp']
            }

            yield _sse_msg('complete', result=result, html_content=html_content, progress=100)

        except Exception as e:
            yield _sse_msg('error', f'服务器错误: {e}')

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/search', methods=['POST'])
@login_required
def api_search():
    """API接口：执行商圈搜索"""
    try:
        data = request.get_json()
        city, brands, threshold, required_brands = _validate_search_params(data)

        brand_stores = search_brands(city, brands)

        brands_with_stores = [b for b in brands if brand_stores.get(b)]
        if not brands_with_stores:
            return jsonify({'success': False, 'message': '未找到任何品牌的门店'}), 404

        effective_required = [b for b in required_brands if b in brands_with_stores] if required_brands else None

        clusters = find_clusters(
            {b: brand_stores[b] for b in brands_with_stores},
            threshold,
            required_brands=effective_required
        )

        if not clusters:
            return jsonify({
                'success': False, 'message': '未找到符合条件的商圈',
                'brands_found': brands_with_stores
            }), 404

        result = {
            'success': True, 'city': city, 'brands': brands_with_stores,
            'threshold': threshold, 'cluster_count': len(clusters),
            'clusters': clusters, 'timestamp': datetime.now().isoformat()
        }

        html_content = output_html_string(clusters, city, proxy_mode=True)

        session['last_result'] = {
            'city': city, 'brands': brands_with_stores,
            'cluster_count': len(clusters), 'timestamp': result['timestamp']
        }

        return jsonify({'success': True, 'result': result, 'html_content': html_content})

    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {e}'}), 500


@app.route('/result')
@login_required
def result():
    """结果展示页面"""
    return render_template('result.html')


@app.route('/map')
@login_required
def map_view():
    """地图查看页面"""
    html_content = request.args.get('html', '')
    if not html_content:
        return render_template('map_view.html', html_content='')
    return render_template('map_view.html', html_content=html_content)


@app.route('/_AMapService/<path:path>')
def amap_proxy(path):
    """代理高德 JS API 请求，在服务端附加安全密钥，避免前端暴露 securityJsCode"""
    url = f'https://restapi.amap.com/{path}'
    params = dict(request.args)
    if AMAP_SECURITY_CODE:
        params['jscode'] = AMAP_SECURITY_CODE
    try:
        resp = http_requests.get(url, params=params, timeout=10)
        return Response(resp.content, status=resp.status_code,
                        content_type=resp.headers.get('Content-Type', 'application/json'))
    except Exception:
        return Response('{"error":"proxy request failed"}', status=502,
                        content_type='application/json')


if __name__ == '__main__':
    os.makedirs(app.config['RESULTS_DIR'], exist_ok=True)
    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
