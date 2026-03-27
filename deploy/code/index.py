# -*- coding: utf-8 -*-
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入 Flask 应用
from app import app

def handler(environ, start_response):
    """
    阿里云函数计算入口函数
    将 FC 的 environ 转换为 WSGI 格式
    """
    # 处理 API Gateway 路径
    context = environ.get('fc.context', {})
    
    # 获取请求路径
    path = environ.get('PATH_INFO', '/')
    
    # 处理函数计算的路径前缀
    if path.startswith('/2016-08-15/proxy/'):
        # 移除函数计算的路径前缀
        parts = path.split('/', 5)
        if len(parts) >= 5:
            path = '/' + parts[-1] if parts[-1] else '/'
    
    environ['PATH_INFO'] = path
    
    # 调用 Flask WSGI 应用
    return app(environ, start_response)
