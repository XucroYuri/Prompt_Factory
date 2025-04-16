# 模型管理模块

## 概述

模型管理模块(`model_manager.py`)负责AI模型管理和调用，支持多服务提供商，通过统一接口简化接入和使用。

## 核心类

### ModelProvider

服务提供商基类，定义通用接口和方法。

```python
class ModelProvider:
    def __init__(self, provider_id: str, name: str, api_url: str, cache_dir: str = DEFAULT_CACHE_DIR)
    def fetch_models(self, api_key: str) -> Optional[List[Dict[str, Any]]]
    def _get_headers(self, api_key: str) -> Dict[str, str]
    def _process_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]
```

### 已实现的提供商

- **OpenAIProvider**: OpenAI提供商
- **OpenRouterProvider**: OpenRouter提供商

### ModelManager

模型管理器，负责获取和管理各服务提供商的模型。

```python
class ModelManager:
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR)
    def register_provider(self, provider: ModelProvider) -> None
    def get_models(self, provider_id: str, api_key: str, force_refresh: bool = False) -> List[Dict[str, Any]]
    def get_all_models(self, api_keys: Dict[str, str], force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]
    def parse_model_id(self, model_id: str) -> Tuple[str, str]
    def get_model_info(self, model_id: str, all_models: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]
    def display_models(self, models: List[Dict[str, Any]], provider_name: str = "") -> None
    def display_all_models(self, all_models: Dict[str, List[Dict[str, Any]]]) -> None
```

## 使用示例

```python
# 创建模型管理器
manager = ModelManager()

# 获取所有提供商的模型列表
api_keys = {
    "openai": "your_openai_api_key",
    "openrouter": "your_openrouter_api_key"
}
all_models = manager.get_all_models(api_keys)

# 显示所有模型
manager.display_all_models(all_models)

# 注册自定义提供商
class CustomProvider(ModelProvider):
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        super().__init__(
            provider_id="custom",
            name="Custom Provider",
            api_url="https://api.custom.ai/models",
            cache_dir=cache_dir
        )
    
    def _process_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 实现处理逻辑
        pass

manager.register_provider(CustomProvider())
```

## 扩展计划

### Gemini提供商支持

计划实现Google Gemini提供商：

```python
class GeminiProvider(ModelProvider):
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        super().__init__(
            provider_id="gemini",
            name="Google Gemini",
            api_url="https://api.gemini.ai/models",  # 示例URL
            cache_dir=cache_dir
        )
    
    def fetch_models(self, api_key: str) -> Optional[List[Dict[str, Any]]]:
        # 使用Google Gemini SDK
        from google import genai
        client = genai.Client(api_key=api_key)
        # 获取可用模型列表
        # ...

    def _process_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 实现处理逻辑
        pass
```

### 速率管理机制

基于模型限制控制API请求频率：

- RPM: 每分钟请求数
- TPM: 每分钟令牌数
- RPD: 每日请求数

实现方案将包括：
- 令牌使用统计
- 安全暂停机制
- 随机时间间隔
- 阈值控制（RPM≤50%±10%, TPM≤80%±5%, RPD≤80%±5%）


// 默认服务商及模型
+## 默认服务提供商及模型
+Prompt Factory 现默认将 DeepSeek 作为首选服务提供商，默认模型为 deepseek-chat。
+
+支持的服务提供商（按优先顺序）：
+- DeepSeek（默认，模型 deepseek-chat）
+- OpenAI
+- OpenRouter
+
+在未指定 provider/model_name 时，默认使用 deepseek/deepseek-chat。