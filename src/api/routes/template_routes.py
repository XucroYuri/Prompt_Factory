"""模板管理路由模块

提供模板管理相关的API端点。
"""

from flask import Blueprint, jsonify, request
import logging
import os
import sys
from typing import Dict, List, Any, Optional

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.core.template_manager import TemplateManager

# 设置日志
logger = logging.getLogger('template_routes')

# 创建蓝图
template_bp = Blueprint('templates', __name__)

# 初始化模板管理器实例
template_manager = TemplateManager()

@template_bp.route('/', methods=['GET'])
def get_templates():
    """获取所有可用模板列表
    
    Returns:
        JSON响应，包含模板列表
    """
    try:
        templates = template_manager.get_available_templates()
        return jsonify({
            'status': 'success',
            'data': {
                'templates': templates
            }
        })
    except Exception as e:
        logger.error(f"获取模板列表时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取模板列表失败: {str(e)}"
        }), 500

@template_bp.route('/<template_name>', methods=['GET'])
def get_template(template_name: str):
    """获取指定模板的内容
    
    Args:
        template_name: 模板名称
        
    Returns:
        JSON响应，包含模板内容
    """
    try:
        template_content = template_manager.load_template(template_name)
        if template_content is None:
            return jsonify({
                'status': 'error',
                'message': f"模板 {template_name} 不存在"
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'name': template_name,
                'content': template_content
            }
        })
    except Exception as e:
        logger.error(f"获取模板 {template_name} 时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取模板失败: {str(e)}"
        }), 500

@template_bp.route('/current', methods=['GET'])
def get_current_template():
    """获取当前激活的模板
    
    Returns:
        JSON响应，包含当前模板内容
    """
    try:
        template_content = template_manager.get_current_template()
        if template_content is None:
            return jsonify({
                'status': 'error',
                'message': "当前没有激活的模板"
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'name': template_manager.active_template,
                'content': template_content
            }
        })
    except Exception as e:
        logger.error(f"获取当前模板时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"获取当前模板失败: {str(e)}"
        }), 500

@template_bp.route('/validate', methods=['POST'])
def validate_template():
    """验证模板内容是否有效
    
    请求体:
        {"content": "模板内容"}
        
    Returns:
        JSON响应，包含验证结果
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'status': 'error',
                'message': "请求体中缺少content字段"
            }), 400
            
        content = data['content']
        is_valid = template_manager.validate_template(content)
        
        return jsonify({
            'status': 'success',
            'data': {
                'is_valid': is_valid
            }
        })
    except Exception as e:
        logger.error(f"验证模板时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"验证模板失败: {str(e)}"
        }), 500