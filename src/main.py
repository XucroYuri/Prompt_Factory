"""Prompt Factory 主程序入口

提供命令行接口启动API服务器或直接调用核心功能。
"""

import os
import sys
import argparse
import logging
import importlib
import platform
from typing import Dict, Any, Optional, List, Tuple

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
src_dir = os.path.dirname(current_file)
project_root = os.path.dirname(src_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入操作系统相关工具
from src.utils.environment import get_os_type, get_path_separator, OS_TYPE_WINDOWS, OS_TYPE_MACOS, OS_TYPE_LINUX

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('prompt_factory')


def check_environment() -> Tuple[bool, List[str], Dict[str, Any]]:
    """检查运行环境和依赖
    
    检查必要的Python包是否已安装，以及其他运行环境要求
    
    Returns:
        Tuple[bool, List[str], Dict[str, Any]]: 是否满足要求，缺失的依赖列表，环境信息
    """
    missing_deps = []
    required_packages = [
        'requests',  # 网络请求
        'flask',     # API服务器
        'json',      # JSON处理
    ]
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_deps.append(package)
    
    # 检测操作系统类型
    os_type = get_os_type()
    path_sep = get_path_separator()
    
    env_info = {
        "os_type": os_type,
        "path_separator": path_sep,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    return len(missing_deps) == 0, missing_deps, env_info


# 导入核心模块
try:
    from src.core.template_manager import TemplateManager
    from src.core.config_manager import ConfigManager
    from src.core.model_manager import ModelManager
    from src.core.prompt_processor import PromptProcessor, ProcessingError
except ImportError as e:
    logger.error(f"无法导入核心模块: {e}")
    print(f"错误: 无法导入核心模块: {e} / Error: Failed to import core modules: {e}")
    print("请确保项目结构完整 / Please ensure project structure is complete")
    sys.exit(1)


def start_api_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """启动API服务器
    
    Args:
        host: 主机地址，默认为0.0.0.0
        port: 端口号，默认为5000
        debug: 是否开启调试模式，默认为False
    """
    try:
        from src.api.server import start_server
        start_server(host=host, port=port, debug=debug)
    except ImportError as e:
        logger.error(f"无法导入API服务器模块: {e}")
        print("启动API服务器失败: 无法导入API服务器模块 / Failed to start API server: Cannot import API server module")
        print("请确保已安装所有依赖: pip install flask / Please make sure all dependencies are installed: pip install flask")
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"API服务器连接错误: {e}")
        print("启动API服务器失败: 网络连接错误 / Failed to start API server: Network connection error")
        sys.exit(1)
    except OSError as e:
        logger.error(f"API服务器操作系统错误: {e}")
        print(f"启动API服务器失败: 端口 {port} 可能已被占用 / Failed to start API server: Port {port} may be in use")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动API服务器时发生未知错误: {e}")
        print("启动API服务器失败: 发生未知错误 / Failed to start API server: Unknown error occurred")
        if debug:
            logger.exception("详细错误信息:")
        sys.exit(1)


def process_content(content: str, api_key: str, template_name: str = 'standard', model: str = 'deepseek/deepseek-chat', output_path: Optional[str] = None, timeout: int = 30, max_retries: int = 2):
    """处理提示词内容
    
    Args:
        content: 要处理的文本内容
        api_key: API密钥
        template_name: 模板名称，默认为standard
        model: 模型ID，默认为deepseek/deepseek-chat
        output_path: 输出路径，默认为None
        timeout: API请求超时时间（秒），默认30秒
        max_retries: API请求失败后的最大重试次数，默认2次
        
    Returns:
        str: 处理结果
    """
    try:
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path,
            timeout=timeout,
            max_retries=max_retries
        )
        return processor.process_content(content)
    except ProcessingError as e:
        logger.error(f"处理内容时出错: {e}")
        if hasattr(e, 'details') and e.details:
            logger.error(f"错误详情: {e.details}")
        return None


def process_file(file_path: str, api_key: str, template_name: str = 'standard', model: str = 'deepseek/deepseek-chat', output_path: Optional[str] = None, timeout: int = 30, max_retries: int = 2):
    """处理文件
    
    Args:
        file_path: 文件路径
        api_key: API密钥
        template_name: 模板名称，默认为standard
        model: 模型ID，默认为deepseek/deepseek-chat
        output_path: 输出路径，默认为None
        timeout: API请求超时时间（秒），默认30秒
        max_retries: API请求失败后的最大重试次数，默认2次
        
    Returns:
        bool: 处理是否成功
    """
    # 标准化文件路径，确保在不同操作系统下都能正确处理
    file_path = os.path.normpath(file_path)
    try:
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path,
            timeout=timeout,
            max_retries=max_retries
        )
        return processor.process_file(file_path)
    except ProcessingError as e:
        logger.error(f"处理文件时出错: {e}")
        if hasattr(e, 'details') and e.details:
            logger.error(f"错误详情: {e.details}")
        return False


def process_directory(directory_path: str, api_key: str, template_name: str = 'standard', model: str = 'deepseek/deepseek-chat', output_path: Optional[str] = None, timeout: int = 30, max_retries: int = 2):
    """处理目录
    
    Args:
        directory_path: 目录路径
        api_key: API密钥
        template_name: 模板名称，默认为standard
        model: 模型ID，默认为deepseek/deepseek-chat
        output_path: 输出路径，指定结果保存的绝对路径，默认为项目根目录下的output目录
        timeout: API请求超时时间（秒），默认30秒
        max_retries: API请求失败后的最大重试次数，默认2次
        
    Returns:
        Dict[str, Any]: 处理统计结果
    """
    # 标准化目录路径，确保在不同操作系统下都能正确处理
    directory_path = os.path.normpath(directory_path)
    try:
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path,
            timeout=timeout,
            max_retries=max_retries
        )
        return processor.process_directory(directory_path)
    except ProcessingError as e:
        logger.error(f"处理目录时出错: {e}")
        if hasattr(e, 'details') and e.details:
            logger.error(f"错误详情: {e.details}")
        return None


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='Prompt Factory 命令行工具 / Command Line Tool')
    
    # 配置管理器
    config_manager = ConfigManager()
    api_key = config_manager.get_config_value('api_key', '')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令 / Subcommands')
    
    # API服务器命令
    server_parser = subparsers.add_parser('server', help='启动API服务器 / Start API Server')
    server_parser.add_argument('--host', '-H', type=str, default='0.0.0.0', help='主机地址 / Host Address')
    server_parser.add_argument('--port', '-P', type=int, default=5000, help='端口号 / Port Number')
    server_parser.add_argument('--debug', '-D', action='store_true', help='开启调试模式 / Enable Debug Mode')
    
    # 处理文本命令
    process_parser = subparsers.add_parser('process', help='处理提示词内容 / Process Prompt Content')
    process_parser.add_argument('content', type=str, help='要处理的文本内容 / Text Content to Process')
    process_parser.add_argument('--api-key', '-k', type=str, default=api_key, help='API密钥 / API Key')
    process_parser.add_argument('--template', '-t', type=str, default='standard', help='模板名称 / Template Name')
    process_parser.add_argument('--model', '-m', type=str, default='deepseek/deepseek-chat', help='模型ID / Model ID')
    process_parser.add_argument('--timeout', type=int, default=30, help='API请求超时时间（秒）/ API Request Timeout (seconds)')
    process_parser.add_argument('--max-retries', type=int, default=2, help='API请求失败后的最大重试次数 / Maximum Retry Count after API Failure')
    
    # 处理文件命令
    file_parser = subparsers.add_parser('file', help='处理文件 / Process File')
    file_parser.add_argument('file_path', type=str, help='文件路径 / File Path')
    file_parser.add_argument('--api-key', '-k', type=str, default=api_key, help='API密钥 / API Key')
    file_parser.add_argument('--template', '-t', type=str, default='standard', help='模板名称 / Template Name')
    file_parser.add_argument('--model', '-m', type=str, default='deepseek/deepseek-chat', help='模型ID / Model ID')
    file_parser.add_argument('--timeout', type=int, default=30, help='API请求超时时间（秒）/ API Request Timeout (seconds)')
    file_parser.add_argument('--max-retries', type=int, default=2, help='API请求失败后的最大重试次数 / Maximum Retry Count after API Failure')
    
    # 处理目录命令
    dir_parser = subparsers.add_parser('dir', help='处理目录 / Process Directory')
    dir_parser.add_argument('directory_path', type=str, help='目录路径 / Directory Path')
    dir_parser.add_argument('--api-key', '-k', type=str, default=api_key, help='API密钥 / API Key')
    dir_parser.add_argument('--template', '-t', type=str, default='standard', help='模板名称 / Template Name')
    dir_parser.add_argument('--model', '-m', type=str, default='deepseek/deepseek-chat', help='模型ID / Model ID')
    dir_parser.add_argument('--timeout', type=int, default=30, help='API请求超时时间（秒）/ API Request Timeout (seconds)')
    dir_parser.add_argument('--max-retries', type=int, default=2, help='API请求失败后的最大重试次数 / Maximum Retry Count after API Failure')
    
    # 解析参数
    args = parser.parse_args()
    
    if args.command == 'server':
        print(f"启动API服务器 - 地址: {args.host}:{args.port} / Starting API Server - Address: {args.host}:{args.port}")
        start_api_server(host=args.host, port=args.port, debug=args.debug)
    elif args.command == 'process':
        if not args.api_key:
            print("错误: 缺少API密钥 / Error: Missing API Key")
            sys.exit(1)
        result = process_content(args.content, args.api_key, args.template, args.model, timeout=args.timeout, max_retries=args.max_retries)
        if result:
            print(result)
        else:
            print("处理内容失败 / Content processing failed")
            sys.exit(1)
    elif args.command == 'file':
        if not args.api_key:
            print("错误: 缺少API密钥 / Error: Missing API Key")
            sys.exit(1)
        success = process_file(args.file_path, args.api_key, args.template, args.model, timeout=args.timeout, max_retries=args.max_retries)
        if success:
            print(f"文件 {args.file_path} 处理成功 / File {args.file_path} processed successfully")
        else:
            print(f"处理文件 {args.file_path} 失败 / Failed to process file {args.file_path}")
            sys.exit(1)
    elif args.command == 'dir':
        if not args.api_key:
            print("错误: 缺少API密钥 / Error: Missing API Key")
            sys.exit(1)
        stats = process_directory(args.directory_path, args.api_key, args.template, args.model, timeout=args.timeout, max_retries=args.max_retries)
        if stats:
            print(f"目录处理完成: 总计 {stats['total']} 个文件，成功 {stats['success']} 个，失败 {stats['failed']} 个，跳过 {stats['skipped']} 个")
            print(f"Directory processed: Total {stats['total']} files, {stats['success']} successful, {stats['failed']} failed, {stats['skipped']} skipped")
            if stats['failed'] > 0 and stats['failed_files']:
                print("失败的文件: / Failed files:")
                for failed_file in stats['failed_files']:
                    print(f"  - {failed_file}")
        else:
            print(f"处理目录 {args.directory_path} 失败 / Failed to process directory {args.directory_path}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()