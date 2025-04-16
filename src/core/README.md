# 核心模块

## 概述

核心模块包含Prompt Factory的主要功能组件，采用模块化设计确保可扩展性。

## 模块列表

### model_manager.py

提供AI模型管理和调用功能，支持多种服务提供商。

- 已支持提供商：DeepSeek（默认）、OpenAI、OpenRouter
- 提供模型查询、缓存和服务提供商统一抽象接口
- 支持自定义服务提供商扩展

### prompt_processor.py

处理提示词核心逻辑，实现提示优化和批处理能力。

- 支持单文件/目录批量处理
- 自动应用模板转换提示词
- 结果缓存与导出

### template_manager.py

管理提示词模板的加载、验证和应用。

- 提供模板格式验证
- 支持自定义模板扩展
- 确保模板中包含必要的占位符

### config_manager.py

配置管理，提供统一的配置访问接口。

- 安全的API密钥管理
- 用户偏好设置
- 应用运行时配置

```
- 默认模型：deepseek-chat（DeepSeek）、其他如OpenAI/gpt-3.5-turbo、OpenRouter/compatible