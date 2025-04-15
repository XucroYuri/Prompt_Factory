"""增强的命令行入口

提供自动化启动流程，包括环境检测、依赖安装、用户交互配置和API连接测试。
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple

# 设置基本日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('enhanced_cli')

# 导入工具模块
from src.utils.environment import (
    setup_environment, validate_api_key, clear_sensitive_data, 
    sanitize_log_message, create_secure_log_handler
)
from src.utils.cli_interface import (
    print_header, print_success, print_error, print_warning, print_info,
    collect_api_keys, select_provider, select_model, select_template,
    select_input_path, select_output_path, show_summary, interactive_setup
)

# 导入核心模块
from src.core.model_manager import ModelManager
from src.core.template_manager import TemplateManager
from src.core.prompt_processor import PromptProcessor, ProcessingError


def run_startup_sequence(args: argparse.Namespace) -> bool:
    """运行启动序列
    
    执行环境检测、依赖安装、目录创建等启动前准备工作
    
    Args:
        args: 命令行参数
    
    Returns:
        bool: 启动序列是否成功完成
    """
    print_header("Prompt Factory - 启动序列")
    print_info("正在检查环境并准备必要组件...")
    
    # 设置环境（检查Python版本、安装依赖、创建目录）
    success, env_info = setup_environment(force_install=args.force_install, auto_fix=True)
    
    if not success:
        print_error("环境设置失败，请检查日志获取详细信息")
        if "setup_error" in env_info:
            print_error(f"错误原因: {env_info['setup_error']}")
        return False
    
    # 显示环境信息
    print_success("环境检查完成")
    print_info(f"Python版本: {env_info['python_version']}")
    
    # 显示依赖信息
    if env_info['dependencies']['required']['all_installed']:
        print_success("所有必需依赖已安装")
    else:
        missing = env_info['dependencies']['required']['missing']
        print_warning(f"缺少必需依赖: {', '.join(missing)}")
    
    return True


def test_api_connection(api_keys: Dict[str, str]) -> Dict[str, bool]:
    """测试API连接
    
    Args:
        api_keys: API密钥字典
    
    Returns:
        Dict[str, bool]: 各服务提供商的连接测试结果
    """
    print_header("API连接测试")
    results = {}
    
    # 测试各提供商的API连接
    for provider, api_key in api_keys.items():
        print_info(f"正在测试 {provider} API连接...")
        try:
            success = validate_api_key(api_key, provider)
            results[provider] = success
            
            if success:
                print_success(f"{provider} API连接成功")
            else:
                print_error(f"{provider} API连接失败")
                
        except Exception as e:
            print_error(f"{provider} API连接时出错: {e}")
            results[provider] = False
    
    return results


def process_files(config: Dict[str, Any]) -> bool:
    """处理文件
    
    Args:
        config: 配置信息
    
    Returns:
        bool: 处理是否成功
    """
    try:
        # 创建处理器
        processor = PromptProcessor(
            api_key=config["api_key"],
            template_name=config.get("template", "standard"),
            model=config.get("model", "openai/gpt-3.5-turbo"),
            output_path=config.get("output_path")
        )
        
        # 处理输入路径
        input_path = config["input_path"]
        if os.path.isdir(input_path):
            # 处理目录
            print_info(f"正在处理目录: {input_path}")
            stats = processor.process_directory(input_path)
            show_summary(stats)
            return stats.get("failed", 0) == 0
            
        else:
            # 处理单个文件
            print_info(f"正在处理文件: {input_path}")
            result = processor.process_file(input_path)
            
            if result:
                print_success("文件处理成功")
            else:
                print_error("文件处理失败")
                
            return result
            
    except ProcessingError as e:
        print_error(f"处理过程中出错: {e}")
        if hasattr(e, 'details') and e.details:
            print_error(f"错误详情: {e.details}")
        return False
    except Exception as e:
        print_error(f"未知错误: {e}")
        return False


def collect_configuration() -> Dict[str, Any]:
    """收集用户配置
    
    与用户进行交互，收集处理所需的配置信息
    
    Returns:
        Dict[str, Any]: 配置信息
    """
    # 获取基本设置（API密钥等）
    config = interactive_setup()
    if not config:
        return {}
    
    # 测试API连接
    connection_results = test_api_connection({config["provider"]: config["api_key"]})
    if not connection_results.get(config["provider"], False):
        if not input("API连接测试失败，是否继续？(y/n): ").lower().startswith('y'):
            return {}
    
    # 获取模型列表
    print_info("正在获取可用模型列表...")
    model_manager = ModelManager()
    all_models = model_manager.get_all_models({config["provider"]: config["api_key"]})
    provider_models = all_models.get(config["provider"], [])
    
    if provider_models:
        # 选择模型
        model = select_model(config["provider"], provider_models)
        if model:
            config["model"] = f"{config['provider']}/{model}"
    else:
        print_warning(f"无法获取{config['provider']}的模型列表，将使用默认模型")
    
    # 获取模板列表
    template_manager = TemplateManager()
    templates = template_manager.list_templates()
    template = select_template(templates)
    if template:
        config["template"] = template
    
    # 获取输入路径
    config["input_path"] = select_input_path("请输入要处理的文件或目录路径")
    
    # 获取输出路径（可选）
    output_path = select_output_path("请输入结果输出目录路径（可选，留空使用默认路径）")
    if output_path:
        config["output_path"] = output_path
    
    return config


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Prompt Factory - 增强的提示词处理工具")
    parser.add_argument("--force-install", action="store_true", help="强制安装依赖包")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 运行启动序列
        if not run_startup_sequence(args):
            sys.exit(1)
        
        # 收集用户配置
        config = collect_configuration()
        if not config:
            print_error("配置收集失败或已取消")
            sys.exit(1)
        
        # 处理文件或目录
        success = process_files(config)
        
        # 结束程序
        if success:
            print_success("处理完成")
            sys.exit(0)
        else:
            print_error("处理过程中出现错误")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_warning("\n程序已被用户中断")
        sys.exit(130)
    except Exception as e:
        print_error(f"发生未处理的异常: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # 确保清理敏感数据
        clear_sensitive_data()


if __name__ == "__main__":
    main()