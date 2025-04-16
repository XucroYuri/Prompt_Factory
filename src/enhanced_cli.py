"""增强的命令行入口

提供自动化启动流程，包括环境检测、依赖安装、用户交互配置和API连接测试。
"""

import os
import sys
import time
import logging
import argparse
import platform
from typing import Dict, List, Any, Optional, Tuple

# 导入操作系统相关工具
import sys
import os

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
src_dir = os.path.dirname(current_file)
project_root = os.path.dirname(src_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入操作系统相关工具
from src.utils.environment import get_os_type, get_path_separator, OS_TYPE_WINDOWS, OS_TYPE_MACOS, OS_TYPE_LINUX
# 导入任务管理器
from src.utils.task_manager import TaskManager

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
    select_input_path, select_output_path, show_summary, interactive_setup,
    get_confirmation
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
        
    # 显示操作系统信息
    os_type = env_info.get('os_type', get_os_type())
    print_info(f"检测到操作系统类型: {os_type}")
    if os_type == OS_TYPE_WINDOWS:
        print_info("Windows环境下请使用反斜杠(\\)作为路径分隔符")
    else:
        print_info("Unix-like环境下请使用正斜杠(/)作为路径分隔符")
    
    return True


def test_api_connection(api_keys: Dict[str, str], timeout: int = 10, max_retries: int = 2) -> Dict[str, bool]:
    """测试API连接
    
    Args:
        api_keys: API密钥字典
        timeout: API请求超时时间（秒），默认10秒
        max_retries: API请求失败后的最大重试次数，默认2次
    
    Returns:
        Dict[str, bool]: 各服务提供商的连接测试结果
    """
    print_header("API连接测试")
    results = {}
    
    # 测试各提供商的API连接
    for provider, api_key in api_keys.items():
        print_info(f"正在测试 {provider} API连接... / Testing {provider} API connection...")
        try:
            success = validate_api_key(api_key, provider, timeout=timeout, max_retries=max_retries)
            results[provider] = success
            
            if success:
                print_success(f"{provider} API连接成功 / {provider} API connection successful")
            else:
                print_error(f"{provider} API连接失败 / {provider} API connection failed")
                
        except Exception as e:
            print_error(f"{provider} API连接时出错: {e} / Error connecting to {provider} API: {e}")
            results[provider] = False
    
    return results


def process_files(config: Dict[str, Any]) -> bool:
    """处理文件
    
    Args:
        config: 配置信息
    
    Returns:
        bool: 处理是否成功
    """
    # 创建任务管理器
    task_manager = TaskManager()
    
    # 检查是否有未完成的任务
    unfinished_task = task_manager.load_latest_task()
    if unfinished_task and unfinished_task.input_path == config["input_path"]:
        # 询问用户是否继续未完成的任务
        if get_confirmation(f"发现未完成的任务（进度: {unfinished_task.get_progress_percentage():.1f}%），是否继续？", default=True):
            print_info("继续处理未完成的任务...")
            # 获取未处理的文件列表
            unfinished_files = task_manager.get_unfinished_files()
            print_info(f"剩余 {len(unfinished_files)} 个文件待处理")
        else:
            # 用户选择不继续，创建新任务
            unfinished_task = None
    else:
        unfinished_task = None
    
    try:
        # 创建处理器
        processor = PromptProcessor(
            api_key=config["api_key"],
            template_name=config.get("template", "standard"),
            model=config.get("model", "openai/gpt-3.5-turbo"),
            output_path=config.get("output_path"),
            timeout=config.get("timeout", 30),
            max_retries=config.get("max_retries", 2)
        )
        
        # 处理输入路径
        input_path = config["input_path"]
        output_path = config.get("output_path", processor.output_path)
        
        # 如果没有未完成任务，创建新任务
        if not unfinished_task:
            task_manager.create_task(input_path, output_path)
        
        if os.path.isdir(input_path):
            # 处理目录
            print_info(f"正在处理目录: {input_path}")
            print_info("处理进度将实时显示在终端...")
            
            # 获取目录中的文件总数（用于进度显示）
            total_files = 0
            for root, _, files in os.walk(input_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    # 跳过已优化的文件
                    if "_optimized" not in file and (not processor.file_extensions or file_ext in processor.file_extensions):
                        total_files += 1
            
            # 设置任务总文件数
            task_manager.current_task.stats["total"] = total_files
            
            # 设置进度显示
            task_manager.setup_progress_display()
            
            # 自定义文件处理回调函数
            def file_callback(file_path: str, success: bool) -> None:
                # 更新任务进度
                task_manager.update_progress(file_path, success)
            
            # 自定义文件跳过回调函数
            def skip_callback(file_path: str) -> None:
                # 标记文件为跳过
                task_manager.skip_file(file_path)
            
            # 处理目录（传入回调函数）
            try:
                stats = processor.process_directory(input_path, callbacks={
                    "file_processed": file_callback,
                    "file_skipped": skip_callback
                })
                
                # 完成任务
                final_stats = task_manager.complete_task()
                
                # 显示处理摘要
                show_summary(stats)
                
                # 生成并显示报告
                task_manager.display_report(final_stats)
                
                # 保存报告
                report_file = task_manager.save_report(final_stats)
                if report_file:
                    print_info(f"任务报告已保存到: {report_file}")
                
                return stats.get("failed", 0) == 0
                
            except KeyboardInterrupt:
                # 用户中断任务
                print_warning("\n任务已被用户中断，正在保存进度...")
                task_manager.pause_task()
                print_info("进度已保存，可以稍后继续处理")
                return False
            
        else:
            # 处理单个文件
            print_info(f"正在处理文件: {input_path}")
            result = processor.process_file(input_path)
            
            # 更新任务状态
            if result:
                task_manager.update_progress(input_path, True)
                print_success("文件处理成功")
            else:
                task_manager.update_progress(input_path, False)
                print_error("文件处理失败")
            
            # 完成任务
            final_stats = task_manager.complete_task()
            
            # 显示报告
            task_manager.display_report(final_stats)
            
            return result
            
    except ProcessingError as e:
        print_error(f"处理过程中出错: {e}")
        if hasattr(e, 'details') and e.details:
            print_error(f"错误详情: {e.details}")
        
        # 标记任务为失败
        if task_manager.current_task:
            task_manager.fail_task()
        
        return False
    except Exception as e:
        print_error(f"未知错误: {e}")
        
        # 标记任务为失败
        if task_manager.current_task:
            task_manager.fail_task()
        
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
    parser.add_argument("--resume", action="store_true", help="恢复上次未完成的任务")
    parser.add_argument("--report", action="store_true", help="显示上次任务的报告")
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 运行启动序列
        if not run_startup_sequence(args):
            sys.exit(1)
        
        # 如果用户请求显示上次任务报告
        if args.report:
            task_manager = TaskManager()
            last_task = task_manager.load_latest_task()
            if last_task:
                # 显示上次任务的报告
                stats = last_task.stats.copy()
                stats["elapsed_time"] = last_task.get_elapsed_time()
                stats["output_path"] = last_task.output_path
                task_manager.display_report(stats)
                sys.exit(0)
            else:
                print_error("没有找到上次任务的记录")
                sys.exit(1)
        
        # 如果用户请求恢复上次任务
        if args.resume:
            task_manager = TaskManager()
            last_task = task_manager.load_latest_task()
            if last_task and last_task.status == "paused":
                # 构建配置
                config = {
                    "input_path": last_task.input_path,
                    "output_path": last_task.output_path
                }
                
                # 提示用户输入API密钥
                print_info(f"正在恢复任务: {last_task.task_id}")
                api_keys = collect_api_keys()
                if not api_keys:
                    print_error("未提供任何API密钥，无法恢复任务")
                    sys.exit(1)
                
                # 选择服务提供商
                provider = select_provider(api_keys)
                if not provider:
                    print_error("未选择服务提供商，无法恢复任务")
                    sys.exit(1)
                
                config["provider"] = provider
                config["api_key"] = api_keys[provider]
                
                # 处理文件或目录
                success = process_files(config)
                
                # 结束程序
                if success:
                    print_success("任务恢复并完成")
                    sys.exit(0)
                else:
                    print_error("任务恢复过程中出现错误")
                    sys.exit(1)
            else:
                print_error("没有找到可恢复的任务")
                sys.exit(1)
        
        # 正常流程：收集用户配置
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
        # 尝试保存当前任务状态
        try:
            task_manager = TaskManager()
            if task_manager.current_task:
                task_manager.pause_task()
                print_info("任务进度已保存，可以使用 --resume 参数恢复")
        except Exception:
            pass
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