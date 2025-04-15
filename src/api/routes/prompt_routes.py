"""提示词处理路由模块

提供提示词处理相关的API端点。
"""

from flask import Blueprint, jsonify, request
import logging
import os
import sys
from typing import Dict, List, Any, Optional

# 导入核心模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from src.core.prompt_processor import PromptProcessor, ProcessingError
from src.core.config_manager import ConfigManager

# 设置日志
logger = logging.getLogger('prompt_routes')

# 创建蓝图
prompt_bp = Blueprint('prompts', __name__)

# 初始化配置管理器实例
config_manager = ConfigManager()

@prompt_bp.route('/process', methods=['POST'])
def process_content():
    """处理提示词内容
    
    请求体:
        {
            "content": "要处理的文本内容",
            "api_key": "API密钥",
            "template_name": "模板名称，可选",
            "model": "模型ID，可选",
            "temperature": 温度值，可选,
            "max_tokens": 最大令牌数，可选
        }
        
    Returns:
        JSON响应，包含处理结果
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'status': 'error',
                'message': "请求体中缺少content字段"
            }), 400
            
        # 获取API密钥，优先使用请求提供的，否则使用配置文件中的
        api_key = data.get('api_key') or config_manager.get_config_value('api_key', '')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': "缺少必要的API密钥"
            }), 400
            
        # 获取其他参数
        template_name = data.get('template_name') or config_manager.get_config_value('template_name', 'standard')
        model = data.get('model') or config_manager.get_config_value('model', 'openai/gpt-4.1')
        temperature = data.get('temperature') or config_manager.get_config_value('parameters.temperature', 0.7)
        max_tokens = data.get('max_tokens') or config_manager.get_config_value('parameters.max_tokens', 1000)
        
        # 初始化处理器
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 处理内容
        content = data['content']
        result = processor.process_content(content)
        
        if result is None:
            return jsonify({
                'status': 'error',
                'message': "处理内容失败"
            }), 500
            
        return jsonify({
            'status': 'success',
            'data': {
                'result': result
            }
        })
    except ProcessingError as e:
        logger.error(f"处理内容时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'details': e.details if hasattr(e, 'details') else None
        }), 500
    except Exception as e:
        logger.error(f"处理内容时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"处理内容失败: {str(e)}"
        }), 500

@prompt_bp.route('/file', methods=['POST'])
def process_file():
    """处理文件
    
    请求体:
        {
            "file_path": "文件路径",
            "api_key": "API密钥，可选",
            "template_name": "模板名称，可选",
            "model": "模型ID，可选"
        }
        
    Returns:
        JSON响应，包含处理结果
    """
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                'status': 'error',
                'message': "请求体中缺少file_path字段"
            }), 400
            
        # 获取API密钥，优先使用请求提供的，否则使用配置文件中的
        api_key = data.get('api_key') or config_manager.get_config_value('api_key', '')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': "缺少必要的API密钥"
            }), 400
            
        # 获取其他参数
        template_name = data.get('template_name') or config_manager.get_config_value('template_name', 'standard')
        model = data.get('model') or config_manager.get_config_value('model', 'openai/gpt-4.1')
        output_path = data.get('output_path')
        
        # 初始化处理器
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path
        )
        
        # 处理文件
        file_path = data['file_path']
        success = processor.process_file(file_path)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': f"处理文件 {file_path} 失败"
            }), 500
            
        return jsonify({
            'status': 'success',
            'message': f"文件 {file_path} 处理成功"
        })
    except ProcessingError as e:
        logger.error(f"处理文件时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'details': e.details if hasattr(e, 'details') else None
        }), 500
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"处理文件失败: {str(e)}"
        }), 500

@prompt_bp.route('/directory', methods=['POST'])
def process_directory():
    """处理目录
    
    请求体:
        {
            "directory_path": "目录路径",
            "api_key": "API密钥，可选",
            "template_name": "模板名称，可选",
            "model": "模型ID，可选",
            "output_path": "输出路径，可选，指定结果保存的绝对路径"
        }
        
    Returns:
        JSON响应，包含处理结果统计
    """
    try:
        data = request.get_json()
        if not data or 'directory_path' not in data:
            return jsonify({
                'status': 'error',
                'message': "请求体中缺少directory_path字段"
            }), 400
            
        # 获取API密钥，优先使用请求提供的，否则使用配置文件中的
        api_key = data.get('api_key') or config_manager.get_config_value('api_key', '')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': "缺少必要的API密钥"
            }), 400
            
        # 获取其他参数
        template_name = data.get('template_name') or config_manager.get_config_value('template_name', 'standard')
        model = data.get('model') or config_manager.get_config_value('model', 'openai/gpt-4.1')
        output_path = data.get('output_path')
        
        # 初始化处理器
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path
        )
        
        # 处理目录
        directory_path = data['directory_path']
        stats = processor.process_directory(directory_path)
        
        return jsonify({
            'status': 'success',
            'data': {
                'stats': stats
            }
        })
    except ProcessingError as e:
        logger.error(f"处理目录时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'details': e.details if hasattr(e, 'details') else None
        }), 500
    except Exception as e:
        logger.error(f"处理目录时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"处理目录失败: {str(e)}"
        }), 500