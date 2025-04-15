# Prompt Factory
高效的提示词处理工具，支持批量优化多文件提示词，自动环境配置。

## 功能特性
- 支持多种AI服务提供商API (OpenAI, Anthropic, OpenRouter)
- 自动化环境检测、依赖安装与自检
- 递归处理目录下所有文件
- 安全的API密钥管理，程序退出时自动清理
- 交互式命令行界面
- 模块化设计，易于扩展与集成

## 安装说明
### 依赖要求
- Python 3.8+
- pip 20.0+

### 安装步骤
1. 克隆仓库
   ```bash
   git clone https://github.com/XucroYuri/Prompt_Factory.git
   cd Prompt_Factory
   python -m src.enhanced_cli
   ```
   程序会自动检测环境、安装依赖并引导完成配置。

## 使用流程
1. 运行程序：`python -m src.enhanced_cli`
2. 按提示输入API密钥（支持OpenAI、Anthropic、OpenRouter）
3. 自动测试API连接
4. 选择服务提供商和模型
5. 选择提示词模板
6. 输入要处理的文件或目录路径
7. 处理完成后，结果保存到output目录

## 高级用法
### 命令行参数
```bash
python -m src.enhanced_cli --force-install  # 强制重新安装依赖
python -m src.enhanced_cli --debug          # 启用调试模式
```

### 开发者API
```python
from src.core.prompt_processor import PromptProcessor

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
```

## 支持的模型服务商
- OpenAI
- Anthropic
- OpenRouter

## 目录结构
```
Prompt_Factory/
├── docs/            # 技术文档
├── output/          # 处理结果输出
├── logs/            # 日志文件
├── src/             # 源代码
│   ├── api/         # API服务器
│   ├── core/        # 核心功能模块
│   │   ├── model_manager.py     # 模型管理
│   │   ├── prompt_processor.py  # 提示词处理
│   │   └── template_manager.py  # 模板管理
│   ├── utils/       # 工具函数
│   │   ├── environment.py       # 环境管理
│   │   └── cli_interface.py     # 命令行交互
│   ├── enhanced_cli.py          # 增强命令行入口
│   └── main.py                  # 主程序入口
└── templates/       # 提示词模板
```

## 注意事项
- API密钥仅在内存中使用，程序退出时自动清理
- 处理结果保存在output目录，按日期和批次自动组织
- 日志文件不包含敏感信息，确保API密钥安全
- 建议使用 Python 3.8 或更高版本以确保最佳兼容性

## 开发计划
- 更多模型提供商集成：支持Google Gemini、Grok、DeepSeek等。
- 速率管理机制：实现API通信速率控制。
- 基于时区的运行计划：按时区设置运行时段。
- 前端界面开发：设计直观高效的用户界面。

## 系统架构
### 核心模块及其关系
```
+-------------------+      +------------------+
| PromptProcessor   |----->| TemplateManager  |
| (主处理器)         |      | (模板管理)       |
+-------------------+      +------------------+
         |                          |
         | 调用                      | 加载模板
         v                          v
+-------------------+      +------------------+
| ModelManager      |      | Templates        |
| (模型管理)         |      | (模板文件)       |
+-------------------+      +------------------+
         |
         | 配置访问
         v
+-------------------+
| Config            |
| (配置管理)         |
+-------------------+
```

### 数据流程
1. 用户通过命令行或配置文件提供参数
2. `prompt_processor.py` 加载配置并初始化处理器
3. 处理器通过 `template_manager.py` 加载指定模板
4. 处理器从指定目录读取提示词文件
5. 处理器将提示词插入到模板中进行处理
6. 调用 `model_manager.py` 获取模型并发送请求
7. 处理响应并保存优化后的提示词

## 前后端分离开发指南
后端提供RESTful API接口，详细设计请参考 [API参考文档](/docs/api_reference.md)。前端开发建议和组件设计请参考 [前端集成文档](/docs/frontend_integration.md)。

## 贡献指南
欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：
1. Fork项目
2. 创建新分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add some feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 提交Pull Request

请确保您的代码符合项目代码规范，并且通过了所有测试。

## 许可证
本项目采用MIT许可证。详情请参阅[LICENSE](LICENSE)文件。