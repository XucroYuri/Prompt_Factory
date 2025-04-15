"""API服务器模块

提供REST API接口的Flask服务器实现。
"""

from flask import Flask, jsonify, request
import logging
import os
import sys

# 确保可以导入src目录下的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api_server')

# 创建Flask应用
app = Flask(__name__)

# 导入路由
from .routes import template_routes, config_routes, model_routes, prompt_routes

# 注册路由蓝图
app.register_blueprint(template_routes.template_bp, url_prefix='/api/templates')
app.register_blueprint(config_routes.config_bp, url_prefix='/api/config')
app.register_blueprint(model_routes.model_bp, url_prefix='/api/models')
app.register_blueprint(prompt_routes.prompt_bp, url_prefix='/api/prompts')

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': '资源不存在',
        'code': 404
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'status': 'error',
        'message': '服务器内部错误',
        'code': 500
    }), 500

# API入口路由
@app.route('/api', methods=['GET'])
def api_index():
    return jsonify({
        'status': 'success',
        'message': 'Prompt Factory API服务',
        'version': '0.1.0',
        'endpoints': [
            '/api/templates',
            '/api/config',
            '/api/models',
            '/api/prompts'
        ]
    })

def start_server(host='0.0.0.0', port=5000, debug=False):
    """启动API服务器
    
    Args:
        host: 主机地址，默认为0.0.0.0
        port: 端口号，默认为5000
        debug: 是否开启调试模式，默认为False
    """
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    start_server(debug=True)