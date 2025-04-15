# Prompt Factory API 参考

## 核心接口

### 1. 模板管理 (TemplateManager)

#### 1.1 获取模板列表

```python
def get_available_templates() -> List[str]
```

**返回**: 模板名称列表。

#### 1.2 加载模板

```python
def load_template(template_name: str = "standard") -> Optional[str]
```

**参数**:
- `template_name`: 模板名称，默认 "standard"。

**返回**: 模板内容，若不存在则为 None。

#### 1.3 获取当前模板

```python
def get_current_template() -> Optional[str]
```

**返回**: 当前模板内容，若无激活模板则为 None。

#### 1.4 验证模板

```python
def validate_template(template_content: str) -> bool
```

**参数**:
- `template_content`: 待验证模板内容。

**返回**: 布尔值，模板是否有效。

### 2. 配置管理 (config.py)

#### 2.1 加载配置

```python
def load_config() -> Dict[str, Any]
```

**返回**: 配置信息字典。

#### 2.2 保存配置

```python
def save_config(config: Dict[str, Any]) -> bool
```

**参数**:
- `config`: 配置信息字典。

**返回**: 布尔值，保存是否成功。

#### 2.3 更新配置

```python
def update_config(key: str, value: Any) -> bool
```

**参数**:
- `key`: 配置键名。
- `value`: 配置值。

**返回**: 布尔值，更新是否成功。

#### 2.4 获取配置值

```python
def get_config_value(key: str, default: Any = None) -> Any
```

**参数**:
- `key`: 配置键名。
- `default`: 默认值，键不存在时返回。

**返回**: 配置值。

### 3. 模型管理 (ModelManager)

#### 3.1 创建实例

```python
model_manager = ModelManager()
```

#### 3.2 获取模型列表

```python
def get_models(provider_id: str, api_key: str, force_refresh: bool = False) -> List[Dict]
```

**参数**:
- `provider_id`: 服务提供商ID，如 "openai"、"openrouter"、"deepseek"
- `api_key`: API密钥
- `force_refresh`: 是否强制刷新缓存，默认False

**返回**: 模型列表，每个模型为字典

#### 3.3 获取所有提供商模型

```python
def get_all_models(api_keys: Dict[str, str], force_refresh: bool = False) -> Dict[str, List[Dict]]
```

**参数**:
- `api_keys`: 提供商API密钥字典，格式 {"provider_id": "api_key"}
- `force_refresh`: 是否强制刷新缓存，默认False

**返回**: 模型列表，格式 {"provider_id": models_list}

#### 3.4 获取模型信息

```python
def get_model_info(model_id: str, all_models: Dict[str, List[Dict]]) -> Optional[Dict]
```

**参数**:
- `model_id`: 模型ID，格式 "provider/model_name"
- `all_models`: 所有模型列表

**返回**: 模型信息，若不存在则为None

#### 3.5 解析模型ID

```python
def parse_model_id(model_id: str) -> Tuple[str, str]
```

**参数**:
- `model_id`: 模型ID，格式 "provider/model_name"

**返回**: (provider_id, model_name)元组

#### 3.6 注册提供商

```python
def register_provider(provider: ModelProvider) -> None
```

**参数**:
- `provider`: 服务提供商实例，继承ModelProvider基类

#### 3.7 显示模型列表

```python
def display_models(models: List[Dict], provider_name: str = "") -> None
```

**参数**:
- `models`: 模型列表
- `provider_name`: 提供商名称，可选

#### 3.8 显示所有模型

```python
def display_all_models(all_models: Dict[str, List[Dict]]) -> None
```

**参数**:
- `all_models`: 所有模型列表，格式 {"provider_id": models_list}

### 4. 提示词处理器 (PromptProcessor)

#### 4.1 初始化处理器

```python
def __init__(api_key: str, template_name: str = "standard", model: str = "anthropic/claude-3.7-sonnet", 
             temperature: float = 0.7)
```

**参数**:
- `api_key`: API密钥
- `template_name`: 模板名称，默认standard
- `model`: 使用模型，默认为anthropic/claude-3.7-sonnet
- `temperature`: 输出随机性

#### 4.2 处理单个文件

```python
def process_file(self, file_path: str) -> bool
```

**参数**:
- `file_path`: 需要处理的文件路径。

**返回值**: 布尔值，表示处理是否成功。

#### 4.3 设置模板

```python
def set_template(self, template_name: str) -> bool
```

**参数**:
- `template_name`: 模板名称。

**返回值**: 布尔值，表示是否成功更改模板。

#### 4.4 获取当前模板名称

```python
def get_active_template(self) -> str
```

**返回值**: 当前模板名称。

#### 4.5 处理目录

```python
def process_directory(self, directory_path: str) -> Dict
```

**参数**:
- `directory_path`: 目录路径。

**返回值**: 处理统计结果字典。