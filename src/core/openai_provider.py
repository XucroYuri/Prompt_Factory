# -*- coding: utf-8 -*-

"""
OpenAI API 服务提供商实现
"""

from typing import Dict, List, Optional, Any
import requests
import json
from .model_manager import ModelProvider, DEFAULT_CACHE_DIR
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider(ModelProvider):
    """
    OpenAI API 服务提供商实现
    """

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        super().__init__(
            provider_id="openai",
            name="OpenAI",
            api_url="https://api.openai.com/v1/models",
            cache_dir=cache_dir
        )

    def fetch_models(self, api_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取OpenAI模型列表
        
        Args:
            api_key: API密钥
            
        Returns:
            Optional[List[Dict[str, Any]]]: 模型列表，如果获取失败则返回None
        """
        try:
            endpoint = self.api_url
            headers = self._get_headers(api_key)
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"获取OpenAI模型列表失败，状态码: {response.status_code}")
                return None
                
            data = response.json()
            return self._process_response(data)
            
        except Exception as e:
            logger.error(f"获取OpenAI模型列表时出错: {e}")
            return None

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        """
        构建请求头
        
        Args:
            api_key: API密钥
            
        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def _process_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理API响应，提取并格式化模型信息
        
        Args:
            data: API响应数据
            
        Returns:
            List[Dict[str, Any]]]: 格式化后的模型列表
        """
        models = []
        for model in data.get("data", []):
            model_id = model.get("id")
            if model_id:
                models.append({
                    "id": model_id,
                    "name": model_id,
                    "description": model.get("description", ""),
                    "provider": "openai"
                })
        return models