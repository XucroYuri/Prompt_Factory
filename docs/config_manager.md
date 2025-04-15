# 配置管理模块

## 概述

配置管理模块(`config_manager.py`)负责配置加载、保存和管理，是系统基础组件，确保配置一致性和可访问性。

## 核心类

### ConfigManager

配置管理器，负责加载和保存系统配置。

```python
class ConfigManager:
    def __init__(self, config_path: str = None)
    def load_config(self) -> Dict[str, Any]
    def save_config(self, config: Dict[str, Any]) -> bool
    def update_config(self, key: str, value: Any) -> bool
    def get_config(self, key: str = None) -> Any
    def reset_config(self) -> bool
```

## 功能特性

- **配置加载**: 从文件加载系统配置
- **配置保存**: 将配置保存到文件
- **单项更新**: 更新特定配置项
- **默认值处理**: 提供默认配置
- **嵌套配置**: 支持多层配置结构

## 默认配置

```python
{
    "api_key": "",
    "template_name": "standard",
    "model": "anthropic/claude-3.7-sonnet",
    "default_directory": "",
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 1000
    }
}
```

## 使用示例

```python
# 创建配置管理器
config_manager = ConfigManager()

# 加载配置
config = config_manager.load_config()

# 更新配置
config_manager.update_config("template_name", "concise")
config_manager.update_config("parameters.temperature", 0.8)

# 获取特定配置
api_key = config_manager.get_config("api_key")
temp = config_manager.get_config("parameters.temperature")

# 保存配置
config["model"] = "openai/gpt-4"
config_manager.save_config(config)

# 重置配置
config_manager.reset_config()
```

## 扩展计划

### 速率限制配置

支持模型速率限制配置：

```python
{
    "api_key": "",
    "template_name": "standard",
    "model": "gemini/gemini-2.5-pro",
    "rate_limits": {
        "gemini/gemini-2.5-pro": {
            "rpm": 5,
            "tpm": 1000000,
            "rpd": 25
        }
    }
}
```

### 时区运行配置

支持基于时区的运行配置：

```python
{
    "schedule": {
        "timezone": "Asia/Shanghai",
        "work_hours": [9, 17],
        "custom_ranges": [[10, 12], [14, 16]],
        "enabled": true
    }
}
```