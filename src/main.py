"""Prompt Factory 主程序入口

提供命令行接口启动API服务器或直接调用核心功能。
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('prompt_factory')

# 导入核心模块
from src.core.template_manager import TemplateManager
from src.core.config_manager import ConfigManager
from src.core.model_manager import ModelManager
from src.core.prompt_processor import PromptProcessor, ProcessingError


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
        print("启动API服务器失败: 无法导入API服务器模块")
        print("请确保已安装所有依赖: pip install flask")
        sys.exit(1)


def process_content(content: str, api_key: str, template_name: str = 'standard', model: str = 'openai/gpt-4.1', output_path: Optional[str] = None):
    """处理提示词内容
    
    Args:
        content: 要处理的文本内容
        api_key: API密钥
        template_name: 模板名称，默认为standard
        model: 模型ID，默认为openai/gpt-4.1
        output_path: 输出路径，默认为None
        
    Returns:
        str: 处理结果
    """
    try:
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path
        )
        return processor.process_content(content)
    except ProcessingError as e:
        logger.error(f"处理内容时出错: {e}")
        if hasattr(e, 'details') and e.details:
            logger.error(f"错误详情: {e.details}")
        return None


def process_file(file_path: str, api_key: str, template_name: str = 'standard', model: str = 'openai/gpt-4.1'):
    """处理文件
    
    Args:
        file_path: 文件路径
        api_key: API密钥
        template_name: 模板名称，默认为standard
        model: 模型ID，默认为openai/gpt-4.1
        
    Returns:
        bool: 处理是否成功
    """
    try:
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path
        )
        return processor.process_file(file_path)
    except ProcessingError as e:
        logger.error(f"处理文件时出错: {e}")
        if hasattr(e, 'details') and e.details:
            logger.error(f"错误详情: {e.details}")
        return False


def process_directory(directory_path: str, api_key: str, template_name: str = 'standard', model: str = 'openai/gpt-4.1', output_path: Optional[str] = None):
    """处理目录
    
    Args:
        directory_path: 目录路径
        api_key: API密钥
        template_name: 模板名称，默认为standard
        model: 模型ID，默认为openai/gpt-4.1
        output_path: 输出路径，指定结果保存的绝对路径，默认为项目根目录下的output目录
        
    Returns:
        Dict[str, Any]: 处理统计结果
    """
    try:
        processor = PromptProcessor(
            api_key=api_key,
            template_name=template_name,
            model=model,
            output_path=output_path
        )
        return processor.process_directory(directory_path)
    except ProcessingError as e:
        logger.error(f"处理目录时出错: {e}")
        if hasattr(e, 'details') and e.details:
            logger.error(f"错误详情: {e.details}")
        return None


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='Prompt Factory 命令行工具')
    
    # 配置管理器
    config_manager = ConfigManager()
    api_key = config_manager.get_config_value('api_key', '')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # API服务器命令
    server_parser = subparsers.add_parser('server', help='启动API服务器')
    server_parser.add_argument('--host', '-H', type=str, default='0.0.0.0', help='主机地址')
    server_parser.add_argument('--port', '-P', type=int, default=5000, help='端口号')
    server_parser.add_argument('--debug', '-D', action='store_true', help='开启调试模式')
    
    # 处理文本命令
    process_parser = subparsers.add_parser('process', help='处理提示词内容')
    process_parser.add_argument('content', type=str, help='要处理的文本内容')
    process_parser.add_argument('--api-key', '-k', type=str, default=api_key, help='API密钥')
    process_parser.add_argument('--template', '-t', type=str, default='standard', help='模板名称')
    process_parser.add_argument('--model', '-m', type=str, default='openai/gpt-4.1', help='模型ID')
    
    # 处理文件命令
    file_parser = subparsers.add_parser('file', help='处理文件')
    file_parser.add_argument('file_path', type=str, help='文件路径')
    file_parser.add_argument('--api-key', '-k', type=str, default=api_key, help='API密钥')
    file_parser.add_argument('--template', '-t', type=str, default='standard', help='模板名称')
    file_parser.add_argument('--model', '-m', type=str, default='openai/gpt-4.1', help='模型ID')
    
    # 处理目录命令
    dir_parser = subparsers.add_parser('dir', help='处理目录')
    dir_parser.add_argument('directory_path', type=str, help='目录路径')
    dir_parser.add_argument('--api-key', '-k', type=str, default=api_key, help='API密钥')
    dir_parser.add_argument('--template', '-t', type=str, default='standard', help='模板名称')
    dir_parser.add_argument('--model', '-m', type=str, default='openai/gpt-4.1', help='模型ID')
    
    # 解析参数
    args = parser.parse_args()
    
    if args.command == 'server':
        print(f"启动API服务器 - 地址: {args.host}:{args.port}")
        start_api_server(host=args.host, port=args.port, debug=args.debug)
    elif args.command == 'process':
        if not args.api_key:
            print("错误: 缺少API密钥")
            sys.exit(1)
        result = process_content(args.content, args.api_key, args.template, args.model)
        if result:
            print(result)
        else:
            print("处理内容失败")
            sys.exit(1)
    elif args.command == 'file':
        if not args.api_key:
            print("错误: 缺少API密钥")
            sys.exit(1)
        success = process_file(args.file_path, args.api_key, args.template, args.model)
        if success:
            print(f"文件 {args.file_path} 处理成功")
        else:
            print(f"处理文件 {args.file_path} 失败")
            sys.exit(1)
    elif args.command == 'dir':
        if not args.api_key:
            print("错误: 缺少API密钥")
            sys.exit(1)
        stats = process_directory(args.directory_path, args.api_key, args.template, args.model)
        if stats:
            print(f"目录处理完成: 总计 {stats['total']} 个文件，成功 {stats['success']} 个，失败 {stats['failed']} 个，跳过 {stats['skipped']} 个")
            if stats['failed'] > 0 and stats['failed_files']:
                print("失败的文件:")
                for failed_file in stats['failed_files']:
                    print(f"  - {failed_file}")
        else:
            print(f"处理目录 {args.directory_path} 失败")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()