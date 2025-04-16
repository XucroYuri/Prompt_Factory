"""模型管理模块

提供AI模型管理和调用的功能，支持多种服务提供商。
"""

import os
import json
import time
import requests
from typing import List, Dict, Optional, Tuple, Any, Union, Type
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('model_manager')

# 常量配置
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache")
CACHE_EXPIRY_HOURS = 24


class ModelProvider:
    """模型服务提供商的基类，定义通用接口和方法"""
    
    def __init__(self, provider_id: str, name: str, api_url: str, cache_dir: str = DEFAULT_CACHE_DIR):
        """初始化模型服务提供商
        
        Args:
            provider_id: 服务提供商ID
            name: 服务提供商名称
            api_url: API URL
            cache_dir: 缓存目录
        """
        self.provider_id = provider_id
        self.name = name
        self.api_url = api_url
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, f"{provider_id}_models.json")
    
    def fetch_models(self, api_key: str) -> Optional[List[Dict[str, Any]]]:
        """获取模型列表
        
        Args:
            api_key: API密钥
            
        Returns:
            Optional[List[Dict[str, Any]]]: 模型列表
        """
        try:
            headers = self._get_headers(api_key)
            response = requests.get(self.api_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"获取{self.name}模型列表失败: {response.status_code} - {response.text}")
                return None
            
            return self._process_response(response.json())
            
        except Exception as e:
            logger.error(f"获取{self.name}模型列表时出错: {e}")
            return None
    
    def _get_headers(self, api_key: str) -> Dict[str, str]:
        """获取请求头
        
        Args:
            api_key: API密钥
            
        Returns:
            Dict[str, str]: 请求头
        """
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def _process_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理API响应数据
        
        Args:
            data: API响应数据
            
        Returns:
            List[Dict[str, Any]]: 标准格式的模型列表
        """
        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现_process_response方法")


class ModelManager:
    """模型管理器，负责获取和管理各服务提供商的模型"""
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        """初始化模型管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 初始化服务提供商列表
        self.providers: Dict[str, ModelProvider] = {}
        
        # 注册标准服务提供商
        from .deepseek_provider import DeepSeekProvider
        from .openai_provider import OpenAIProvider
        from .openrouter_provider import OpenRouterProvider
        from .anthropic_provider import AnthropicProvider
        self.register_provider(DeepSeekProvider(cache_dir))
        self.register_provider(OpenAIProvider(cache_dir))
        self.register_provider(OpenRouterProvider(cache_dir))
        self.register_provider(AnthropicProvider(cache_dir))
    
    def register_provider(self, provider: ModelProvider) -> None:
        """注册新的服务提供商
        
        Args:
            provider: 服务提供商实例，需继承自ModelProvider基类
        """
        self.providers[provider.provider_id] = provider
    
    def get_models(self, provider_id: str, api_key: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """获取模型列表
        
        Args:
            provider_id: 服务提供商ID
            api_key: API密钥
            force_refresh: 是否强制刷新缓存，默认为False
            
        Returns:
            List[Dict[str, Any]]: 模型列表，每个模型为一个字典
        """
        if provider_id not in self.providers:
            logger.error(f"未知的服务提供商ID: {provider_id}")
            return []
        
        provider = self.providers[provider_id]
        cache_file = provider.cache_file
        
        # 检查缓存是否存在且未过期
        if not force_refresh and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查缓存是否过期
                cache_time = cache_data.get("timestamp", 0)
                current_time = time.time()
                if current_time - cache_time < CACHE_EXPIRY_HOURS * 3600:
                    return cache_data.get("models", [])
            except Exception as e:
                logger.error(f"读取缓存文件时出错: {e}")
        
        # 获取最新的模型列表
        models = provider.fetch_models(api_key)
        if models is None:
            # 获取失败，尝试使用缓存数据
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    return cache_data.get("models", [])
                except Exception:
                    return []
            return []
            
        # 更新缓存
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": time.time(),
                    "models": models
                }, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存缓存文件时出错: {e}")
            
        return models
    
    def get_all_models(self, api_keys: Dict[str, str], force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有支持的服务提供商的模型列表
        
        Args:
            api_keys: 各服务提供商的API密钥字典，格式为 {"provider_id": "api_key"}
            force_refresh: 是否强制刷新缓存，默认为False
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: 所有模型列表，格式为 {"provider_id": models_list}
        """
        all_models = {}
        for provider_id, api_key in api_keys.items():
            if provider_id in self.providers:
                all_models[provider_id] = self.get_models(provider_id, api_key, force_refresh)
        return all_models
    
    def parse_model_id(self, model_id: str) -> Tuple[str, str]:
        """解析模型ID
        
        Args:
            model_id: 模型ID，格式为 "provider/model_name"
            
        Returns:
            Tuple[str, str]: (provider_id, model_name)元组
        """
        parts = model_id.split('/', 1)
        if len(parts) != 2:
            # 默认视为DeepSeek模型
            return "deepseek", model_id
        return parts[0], parts[1]
    
    def get_model_info(self, model_id: str, all_models: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """获取模型信息
        
        Args:
            model_id: 模型ID，格式为 "provider/model_name"
            all_models: 所有模型列表
            
        Returns:
            Optional[Dict[str, Any]]: 模型信息字典，如果模型不存在则返回None
        """
        provider_id, model_name = self.parse_model_id(model_id)
        
        if provider_id not in all_models:
            return None
            
        provider_models = all_models[provider_id]
        
        for model in provider_models:
            if model.get("id") == model_name or model.get("name") == model_name:
                return model
                
        return None
    
    def display_models(self, models: List[Dict[str, Any]], provider_name: str = "") -> None:
        """显示模型列表
        
        Args:
            models: 模型列表
            provider_name: 服务提供商名称（可选）
        """
        if provider_name:
            print(f"\n=== {provider_name} Models ===")
        
        for model in models:
            print(f"ID: {model.get('id', 'N/A')}")
            print(f"Name: {model.get('name', 'N/A')}")
            print(f"Description: {model.get('description', 'N/A')}")
            print("-" * 40)
    
    def display_all_models(self, all_models: Dict[str, List[Dict[str, Any]]]) -> None:
        """显示所有服务提供商的模型列表
        
        Args:
            all_models: 所有模型列表，格式为 {"provider_id": models_list}
        """
        for provider_id, models in all_models.items():
            provider_name = self.providers.get(provider_id, ModelProvider(provider_id, provider_id, "")).name
            self.display_models(models, provider_name)