# 模板管理模块

## 概述

模板管理模块(`template_manager.py`)负责模板加载、验证和管理，处理系统提示模板，确保提示词处理一致性和可配置性。

## 核心类

### TemplateManager

模板管理器，负责加载和验证系统提示模板。

```python
class TemplateManager:
    def __init__(self, templates_dir: str = None)
    def get_available_templates(self) -> List[str]
    def load_template(self, template_name: str = "standard") -> Optional[str]
    def get_current_template(self) -> Optional[str]
    def validate_template(self, template_content: str) -> bool
```

## 功能特性

- **模板加载**: 从目录加载系统提示模板
- **模板验证**: 验证模板格式及占位符
- **模板缓存**: 缓存模板提升性能
- **灵活配置**: 支持自定义模板目录

## 模板格式

模板文件必须包含以下部分：

1. `## System Message` - 系统消息，定义AI角色和处理逻辑
2. `## User Message` - 用户消息，必须包含`{PROMPT}`占位符

```
## System Message
你是一个专业的提示词优化助手...

## User Message
请帮我优化以下提示词：
{PROMPT}
```

## 使用示例

```python
# 创建模板管理器
manager = TemplateManager()

# 获取可用模板列表
templates = manager.get_available_templates()
print(f"可用模板: {templates}")

# 加载指定模板
template_content = manager.load_template("concise")
if template_content:
    print("模板加载成功")
    
# 验证自定义模板
custom_template = """## System Message\n你是一个AI助手\n\n## User Message\n{PROMPT}"""
if manager.validate_template(custom_template):
    print("自定义模板有效")
```

## 自定义模板

在项目的`templates`目录添加新的.txt文件，确保：

1. 文件名将作为模板名称(如`example.txt`→模板名为`example`)
2. 包含必要的`## System Message`和`## User Message`部分
3. 用户消息部分包含`{PROMPT}`占位符