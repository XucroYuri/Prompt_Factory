# -*- coding: utf-8 -*-

"""
Anthropic API 服务提供商实现
"""

from typing import Dict, List, Optional, Any
import requests
import json
from .model_manager import ModelProvider, DEFAULT_CACHE_DIR
import logging

logger = logging.getLogger(__name__)


class AnthropicProvider(ModelProvider):
    """
    Anthropic API 服务提供商实现
    """

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        super().__init__(
            provider_id="anthropic",
            name="Anthropic",
            api_url="https://api.anthropic.com/v1/models",
            cache_dir=cache_dir
        )

    def fetch_models(self, api_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取Anthropic模型列表
        
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
                logger.error(f"获取Anthropic模型列表失败，状态码: {response.status_code}")
                return None
                
            data = response.json()
            return self._process_response(data)
            
        except Exception as e:
            logger.error(f"获取Anthropic模型列表时出错: {e}")
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
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
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
        for model in data.get("models", []):
            model_id = model.get("name")
            if model_id:
                models.append({
                    "id": model_id,
                    "name": model_id,
                    "description": model.get("description", ""),
                    "provider": "anthropic"
                })
        
        # 确保claude-3.7-sonnet模型可用
        if not any(model["id"] == "claude-3-7-sonnet" for model in models):
            models.append({
                "id": "claude-3-7-sonnet",
                "name": "Claude 3.7 Sonnet",
                "description": "Claude 3.7 Sonnet - Anthropic的高性能语言模型",
                "provider": "anthropic"
            })
        
        return models