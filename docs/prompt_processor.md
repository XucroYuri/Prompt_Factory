# 提示词处理模块

## 概述

提示词处理模块(`prompt_processor.py`)负责提示词加载、处理和生成，是系统核心组件，与AI模型交互并应用模板处理提示词。

## 核心类

### ProcessingError

提示词处理异常类，用于统一异常处理。

```python
class ProcessingError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None)
```

### PromptProcessor

提示词处理器，负责处理和生成提示词。

```python
class PromptProcessor:
    def __init__(self, api_key: str, template_name: str = "standard", 
                 model: str = "anthropic/claude-3.7-sonnet", temperature: float = 0.7, 
                 model_manager: Optional[ModelManager] = None,
                 output_path: Optional[str] = None)
    def process_file(self, file_path: str) -> bool
    def process_content(self, content: str) -> Optional[str]
    def process_directory(self, directory_path: str, recursive: bool = True, 
                          file_extensions: List[str] = None) -> Dict[str, Any]
    def generate_response(self, prompt: str) -> Optional[str]
```

## 功能特性

- **文件处理**: 支持处理单个文件或递归处理目录
- **内容处理**: 将提示词应用到模板并提交给AI模型
- **结果管理**: 保存结果并提供统计
- **错误处理**: 统一错误处理和日志

## 使用示例

```python
# 创建处理器实例
processor = PromptProcessor(
    api_key="your_api_key",
    template_name="standard",
    model="openai/gpt-4"
)

# 处理单个文件
processor.process_file("path/to/file.md")

# 处理整个目录
stats = processor.process_directory(
    "path/to/directory",
    file_extensions=[".md", ".txt"],
    recursive=True
)

# 处理单个提示词
result = processor.process_content("请优化这个提示词")
```

## 扩展计划

### 速率管理集成

计划与模型管理器集成速率控制功能：

```python
class PromptProcessor:
    def __init__(self, api_key: str, template_name: str = "standard", 
                 model: str = "anthropic/claude-3.7-sonnet", temperature: float = 0.7, 
                 model_manager: Optional[ModelManager] = None,
                 output_path: Optional[str] = None,
                 rate_limits: Optional[Dict[str, int]] = None)  # 新增参数
    
    def generate_response(self, prompt: str) -> Optional[str]:
        # 检查速率限制
        if self._check_rate_limits():
            # 添加随机延迟
            self._add_random_delay()
            # 处理请求
            # ...
```

### 时区运行计划

支持基于地理时区设置运行计划：

```python
class PromptProcessor:
    def set_operation_schedule(self, timezone: str, 
                             work_hours: Tuple[int, int] = (9, 17),
                             custom_schedule: Optional[List[Tuple[int, int]]] = None) -> None:
        """设置操作时间计划
        
        Args:
            timezone: 时区标识，如"Asia/Shanghai"
            work_hours: 工作时间范围，默认9点至17点
            custom_schedule: 自定义时间范围列表
        """
        # 实现时区和计划设置逻辑
        # ...
        
    def is_operation_allowed(self) -> bool:
        """检查当前时间是否允许操作
        
        Returns:
            bool: 是否允许操作
        """
        # 检查当前时间是否在允许范围内
        # ...
```