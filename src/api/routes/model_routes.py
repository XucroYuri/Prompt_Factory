"""模型管理路由模块

提供模型管理相关的API端点。
"""

from flask import Blueprint, jsonify, request
import logging
import os
import sys
from typing import Dict, List, Any, Optional

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.core.model_manager import ModelManager

# 设置日志
logger = logging.getLogger('model_routes')

# 创建蓝图
model_bp = Blueprint('models', __name__)

# 初始化模型管理器实例
model_manager = ModelManager()

@model_bp.route('/', methods=['GET'])
def get_models():
    """获取所有模型列表
    
    查询参数:
        provider: 服务提供商ID，如不提供则返回所有提供商的模型
        api_key: API密钥，必须提供
        force_refresh: 是否强制刷新缓存，默认为false
    
    Returns:
        JSON响应，包含模型列表
    """
    try:
        provider = request.args.get('provider')
        api_key = request.args.get('api_key')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': "缺少必要的API密钥参数"
            }), 400
        
        if provider:
            # 获取特定提供商的模型
            models = model_manager.get_models(provider, api_key, force_refresh)
            return jsonify({
                'status': 'success',
                'data': {
                    'provider': provider,
                    'models': models
                }
            })
        else:
            # 获取所有提供商的模型
            all_models = model_manager.get_all_models({p: api_key for p in model_manager.providers.keys()}, force_refresh)
            return jsonify({
                'status': 'success',
                'data': {
                    'providers': list(all_models.keys()),
                    'models': all_models
                }
            })
    except Exception as e:
        logger.error(f"获取模型列表时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取模型列表失败: {str(e)}"
        }), 500

@model_bp.route('/providers', methods=['GET'])
def get_providers():
    """获取所有可用的服务提供商
    
    Returns:
        JSON响应，包含服务提供商列表
    """
    try:
        providers = list(model_manager.providers.keys())
        provider_info = {}
        
        for provider_id in providers:
            provider = model_manager.providers[provider_id]
            provider_info[provider_id] = {
                'name': provider.name,
                'api_url': provider.api_url
            }
        
        return jsonify({
            'status': 'success',
            'data': {
                'providers': providers,
                'provider_info': provider_info
            }
        })
    except Exception as e:
        logger.error(f"获取服务提供商列表时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取服务提供商列表失败: {str(e)}"
        }), 500

@model_bp.route('/<path:model_id>', methods=['GET'])
def get_model_info(model_id: str):
    """获取特定模型的详细信息
    
    Args:
        model_id: 模型ID，格式为 "provider/model_name"
        
    查询参数:
        api_key: API密钥，必须提供
    
    Returns:
        JSON响应，包含模型详细信息
    """
    try:
        api_key = request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': "缺少必要的API密钥参数"
            }), 400
        
        # 解析模型ID
        provider_id, model_name = model_manager.parse_model_id(model_id)
        
        # 获取模型列表
        all_models = {provider_id: model_manager.get_models(provider_id, api_key)}
        
        # 获取模型信息
        model_info = model_manager.get_model_info(model_id, all_models)
        
        if not model_info:
            return jsonify({
                'status': 'error',
                'message': f"模型 {model_id} 不存在"
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'model_id': model_id,
                'provider': provider_id,
                'model_name': model_name,
                'info': model_info
            }
        })
    except Exception as e:
        logger.error(f"获取模型 {model_id} 信息时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取模型信息失败: {str(e)}"
        }), 500