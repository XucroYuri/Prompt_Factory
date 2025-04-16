"""配置管理模块

提供配置加载、保存和管理的功能。
"""

import os
import json
from typing import Dict, Any, Optional, Union, Tuple


class ConfigManager:
    """配置管理器，负责加载和保存系统配置。
    """
    def __init__(self, config_path: str = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录的config.json
        """
        if config_path is None:
            # 使用相对路径，确保在项目中的任何位置都能正确找到配置文件
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.config_path = os.path.join(base_dir, "config.json")
        else:
            self.config_path = config_path
            
        # 默认配置
        self.default_config = {
            "api_key": "",
            "template_name": "standard",
            "model": "anthropic/claude-3.7-sonnet",
            "default_directory": "",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        # 当前配置
        self.config: Dict[str, Any] = {}
        
        # 加载配置
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件。如果配置文件不存在，则创建默认配置文件。
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
            self.config = self.default_config.copy()
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            return self.config
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            self.config = self.default_config.copy()
            return self.config
        except PermissionError as e:
            logger.error(f"无权限读取配置文件: {e}")
            self.config = self.default_config.copy()
            return self.config
        except Exception as e:
            logger.error(f"加载配置文件时发生未知错误: {e}")
            self.config = self.default_config.copy()
            return self.config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件
        
        Args:
            config: 配置信息
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.config = config
            return True
        except Exception:
            return False

    def update_config(self, key: str, value: Any) -> bool:
        """更新单个配置项
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 更新内存中的配置
            if "." in key:
                # 支持嵌套的配置，如 parameters.temperature
                parts = key.split(".")
                current = self.config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                self.config[key] = value
                
            # 保存到文件
            return self.save_config(self.config)
        except Exception:
            return False

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键名
            default: 默认值，当键不存在时返回
            
        Returns:
            Any: 配置值
        """
        try:
            if "." in key:
                # 支持嵌套的配置，如 parameters.temperature
                parts = key.split(".")
                current = self.config
                for part in parts[:-1]:
                    if part not in current:
                        return default
                    current = current[part]
                return current.get(parts[-1], default)
            else:
                return self.config.get(key, default)
        except Exception:
            return default

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证配置是否有效
        
        Args:
            config: 要验证的配置
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        # 验证必须的配置项
        if not isinstance(config.get("model"), str) or not config.get("model"):
            return False, "模型配置无效或缺失"
            
        # 验证参数配置
        parameters = config.get("parameters", {})
        if not isinstance(parameters, dict):
            return False, "parameters必须是字典类型"
            
        if "temperature" in parameters and not (isinstance(parameters["temperature"], (int, float)) and 0 <= parameters["temperature"] <= 1):
            return False, "temperature必须是0到1之间的数值"
            
        if "max_tokens" in parameters and not (isinstance(parameters["max_tokens"], int) and parameters["max_tokens"] > 0):
            return False, "max_tokens必须是正整数"
            
        return True, ""