"""配置管理路由模块

提供配置管理相关的API端点。
"""

from flask import Blueprint, jsonify, request
import logging
import os
import sys
from typing import Dict, List, Any, Optional

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.core.config_manager import ConfigManager

# 设置日志
logger = logging.getLogger('config_routes')

# 创建蓝图
config_bp = Blueprint('config', __name__)

# 初始化配置管理器实例
config_manager = ConfigManager()

@config_bp.route('/', methods=['GET'])
def get_config():
    """获取所有配置
    
    Returns:
        JSON响应，包含完整配置
    """
    try:
        config = config_manager.config
        return jsonify({
            'status': 'success',
            'data': {
                'config': config
            }
        })
    except Exception as e:
        logger.error(f"获取配置时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取配置失败: {str(e)}"
        }), 500

@config_bp.route('/<path:key>', methods=['GET'])
def get_config_value(key: str):
    """获取指定配置项的值
    
    Args:
        key: 配置键名，支持嵌套键，如 parameters.temperature
        
    Returns:
        JSON响应，包含配置值
    """
    try:
        value = config_manager.get_config_value(key)
        if value is None:
            return jsonify({
                'status': 'error',
                'message': f"配置项 {key} 不存在"
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'key': key,
                'value': value
            }
        })
    except Exception as e:
        logger.error(f"获取配置项 {key} 时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取配置项失败: {str(e)}"
        }), 500

@config_bp.route('/', methods=['PUT'])
def update_config():
    """更新多个配置项
    
    请求体:
        {"config": {配置字典}}
        
    Returns:
        JSON响应，包含更新结果
    """
    try:
        data = request.get_json()
        if not data or 'config' not in data:
            return jsonify({
                'status': 'error',
                'message': "请求体中缺少config字段"
            }), 400
            
        config = data['config']
        success = config_manager.save_config(config)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': "配置已更新"
            })
        else:
            return jsonify({
                'status': 'error',
                'message': "更新配置失败"
            }), 500
    except Exception as e:
        logger.error(f"更新配置时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"更新配置失败: {str(e)}"
        }), 500

@config_bp.route('/<path:key>', methods=['PUT'])
def update_config_value(key: str):
    """更新单个配置项
    
    Args:
        key: 配置键名，支持嵌套键，如 parameters.temperature
        
    请求体:
        {"value": 配置值}
        
    Returns:
        JSON响应，包含更新结果
    """
    try:
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({
                'status': 'error',
                'message': "请求体中缺少value字段"
            }), 400
            
        value = data['value']
        success = config_manager.update_config(key, value)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f"配置项 {key} 已更新"
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"更新配置项 {key} 失败"
            }), 500
    except Exception as e:
        logger.error(f"更新配置项 {key} 时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"更新配置项失败: {str(e)}"
        }), 500