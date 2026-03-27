# -*- coding: utf-8 -*-
import sys
import os
import io
import base64

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app

def handler(event, context):
    """
    阿里云函数计算 HTTP 触发器入口函数 (FC 3.0 格式)
    """
    # 解析 FC 3.0 事件格式（支持多种字段名）
    http_method = event.get('httpMethod') or event.get('requestMethod', 'GET')
    path = event.get('path') or event.get('requestPath', '/')
    headers = event.get('headers', {}) or {}
    query_params = event.get('queryParameters', {}) or {}
    body = event.get('body', '')
    is_base64 = event.get('isBase64Encoded', False)
    
    # 解码 body
    if body and is_base64:
        try:
            body = base64.b64decode(body)
        except:
            body = body.encode('utf-8')
    elif body and isinstance(body, str):
        body = body.encode('utf-8')
    
    # 构建查询字符串
    query_string = ''
    if query_params:
        query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
    
    # 构建 WSGI environ
    environ = {
        'REQUEST_METHOD': http_method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'CONTENT_TYPE': headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(body)) if body else '0',
        'SERVER_NAME': headers.get('host', 'localhost').split(':')[0],
        'SERVER_PORT': '80',
        'HTTP_HOST': headers.get('host', ''),
        'HTTP_USER_AGENT': headers.get('user-agent', ''),
        'wsgi.input': io.BytesIO(body) if body else io.BytesIO(b''),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.run_once': True,
        'wsgi.url_scheme': 'https',
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
    }
    
    # 添加其他 HTTP 头
    for key, value in headers.items():
        if value is not None:
            key_upper = key.upper().replace('-', '_')
            if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH', 'HOST', 'USER_AGENT'):
                environ[f'HTTP_{key_upper}'] = value
    
    # 响应容器
    response_status = None
    response_headers = []
    response_body = []
    
    def start_response(status, headers):
        nonlocal response_status, response_headers
        response_status = status
        response_headers = headers
        return response_body.append
    
    # 调用 Flask 应用
    result = app(environ, start_response)
    
    # 收集响应体
    for data in result:
        if data:
            if isinstance(data, bytes):
                response_body.append(data)
            else:
                response_body.append(data.encode('utf-8'))
    
    # 构建 FC 3.0 响应格式
    response_headers_dict = {}
    for k, v in response_headers:
        response_headers_dict[k] = v
    
    full_body = b''.join(response_body)
    
    # 判断是否需要 base64 编码
    is_binary = False
    content_type = response_headers_dict.get('Content-Type', '')
    if 'image' in content_type or 'font' in content_type or 'application/octet-stream' in content_type:
        is_binary = True
    
    if is_binary:
        body_str = base64.b64encode(full_body).decode('utf-8')
        return {
            'statusCode': int(response_status.split()[0]) if response_status else 200,
            'headers': response_headers_dict,
            'body': body_str,
            'isBase64Encoded': True
        }
    else:
        return {
            'statusCode': int(response_status.split()[0]) if response_status else 200,
            'headers': response_headers_dict,
            'body': full_body.decode('utf-8')
        }
