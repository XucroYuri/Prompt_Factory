"""命令行交互模块

提供交互式命令行界面，引导用户进行环境设置、输入必要信息、执行操作。
"""

import os
import sys
import getpass
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('cli_interface')

# 创建Rich控制台对象
console = Console()


def print_header(title: str) -> None:
    """打印带有样式的标题
    
    Args:
        title: 标题文本
    """
    console.print(Panel(f"[bold blue]{title}[/]", expand=False))


def print_success(message: str) -> None:
    """打印成功消息
    
    Args:
        message: 成功消息
    """
    console.print(f"[bold green]✓[/] {message}")


def print_error(message: str) -> None:
    """打印错误消息
    
    Args:
        message: 错误消息
    """
    console.print(f"[bold red]✗[/] {message}")


def print_warning(message: str) -> None:
    """打印警告消息
    
    Args:
        message: 警告消息
    """
    console.print(f"[bold yellow]![/] {message}")


def print_info(message: str) -> None:
    """打印信息消息
    
    Args:
        message: 信息消息
    """
    console.print(f"[bold cyan]i[/] {message}")


def get_input(prompt: str, default: str = "", password: bool = False) -> str:
    """获取用户输入
    
    Args:
        prompt: 提示文本
        default: 默认值
        password: 是否为密码输入
        
    Returns:
        str: 用户输入的文本
    """
    if password:
        return getpass.getpass(prompt=f"{prompt}: ")
    else:
        return Prompt.ask(prompt, default=default)


def get_choice(prompt: str, choices: List[str], default: Optional[str] = None) -> str:
    """获取用户选择
    
    Args:
        prompt: 提示文本
        choices: 选项列表
        default: 默认选项
        
    Returns:
        str: 用户选择的选项
    """
    # 显示选项编号
    console.print(f"\n{prompt}:")
    for i, choice in enumerate(choices):
        console.print(f"  [{i+1}] {choice}")
    
    # 获取用户选择
    while True:
        try:
            default_idx = choices.index(default) + 1 if default in choices else None
            default_str = str(default_idx) if default_idx else ""
            choice_input = Prompt.ask("请输入选项序号", default=default_str)
            choice_idx = int(choice_input) - 1
            
            if 0 <= choice_idx < len(choices):
                return choices[choice_idx]
            else:
                print_error(f"无效的选项序号: {choice_input}")
        except ValueError:
            print_error(f"请输入有效的数字: 1-{len(choices)}")


def get_confirmation(prompt: str, default: bool = False) -> bool:
    """获取用户确认
    
    Args:
        prompt: 提示文本
        default: 默认选项
        
    Returns:
        bool: 用户是否确认
    """
    return Confirm.ask(prompt, default=default)


def collect_api_keys() -> Dict[str, str]:
    """收集各服务提供商的API密钥
    
    Returns:
        Dict[str, str]: API密钥字典
    """
    providers = [
        {"provider": "anthropic", "name": "Anthropic API密钥"},
        {"provider": "deepseek", "name": "DeepSeek API密钥"},
        {"provider": "openai", "name": "OpenAI API密钥"},
        {"provider": "openrouter", "name": "OpenRouter API密钥"},
    ]
    
    api_keys = {}
    print_header("API密钥设置 / API Key Settings")
    print_info("请依次输入各服务提供商的API密钥（输入为空则跳过该提供商）: / Please enter API keys for each provider (skip by leaving empty):")
    
    # 使用providers列表循环获取密钥
    for item in providers:
        key = get_input(f"{item['name']} / {item['provider'].capitalize()} API Key", password=True)
        if key:
            api_keys[item["provider"]] = key
    
    return api_keys


def select_provider(api_keys: Dict[str, str]) -> Optional[str]:
    """选择服务提供商
    
    Args:
        api_keys: API密钥字典
        
    Returns:
        Optional[str]: 选择的服务提供商ID
    """
    if not api_keys:
        print_error("没有可用的API密钥")
        return None
    
    available_providers = list(api_keys.keys())
    if len(available_providers) == 1:
        provider = available_providers[0]
        print_info(f"自动选择唯一可用的服务提供商: {provider}")
        return provider
    
    print_header("选择服务提供商")
    return get_choice("请选择服务提供商", available_providers)


def select_model(provider: str, models: List[Dict[str, Any]]) -> Optional[str]:
    """选择模型
    
    Args:
        provider: 服务提供商ID
        models: 模型列表
        
    Returns:
        Optional[str]: 选择的模型ID
    """
    if not models:
        print_error(f"没有可用的 {provider} 模型")
        return None
    
    print_header("选择模型")
    
    # 显示可用模型
    console.print("可用模型:")
    model_names = []
    for i, model in enumerate(models):
        model_id = model.get("id", "")
        model_name = model.get("name", model_id)
        description = model.get("description", "")
        model_names.append(model_id)
        
        # 截断描述文本
        max_desc_len = 50
        if len(description) > max_desc_len:
            description = description[:max_desc_len] + "..."
        
        console.print(f"  [{i+1}] {model_name} ({model_id})")
        if description:
            console.print(f"      {description}")
    
    # 获取用户选择
    while True:
        try:
            choice_input = Prompt.ask("请输入模型序号")
            choice_idx = int(choice_input) - 1
            
            if 0 <= choice_idx < len(models):
                return models[choice_idx].get("id")
            else:
                print_error(f"无效的模型序号: {choice_input}")
        except ValueError:
            print_error(f"请输入有效的数字: 1-{len(models)}")


def select_template(templates: List[str]) -> Optional[str]:
    """选择模板
    
    Args:
        templates: 模板列表
        
    Returns:
        Optional[str]: 选择的模板名称
    """
    if not templates:
        print_error("没有可用的模板")
        return None
    
    print_header("选择模板")
    return get_choice("请选择提示词模板", templates, default="standard")


def select_input_path(prompt: str = "请输入文件或目录路径") -> str:
    """获取输入路径
    
    Args:
        prompt: 提示文本
        
    Returns:
        str: 输入路径
    """
    while True:
        path = get_input(prompt)
        if os.path.exists(path):
            return os.path.abspath(path)
        else:
            print_error(f"路径不存在: {path}")


def select_output_path(prompt: str = "请输入输出目录路径（可选）", required: bool = False) -> Optional[str]:
    """获取输出路径
    
    Args:
        prompt: 提示文本
        required: 是否必须输入
        
    Returns:
        Optional[str]: 输出路径
    """
    while True:
        path = get_input(prompt)
        if not path and not required:
            return None
        if not path and required:
            print_error("必须输入输出路径")
            continue
        
        # 确保路径存在
        try:
            os.makedirs(path, exist_ok=True)
            return os.path.abspath(path)
        except Exception as e:
            print_error(f"无法创建目录: {e}")


def show_progress(total: int, message: str = "处理中") -> Callable[[int], None]:
    """显示进度条
    
    Args:
        total: 总任务数
        message: 提示消息
        
    Returns:
        Callable[[int], None]: 更新进度的函数
    """
    progress = Progress()
    task = progress.add_task(message, total=total)
    
    def update(n: int):
        progress.update(task, completed=n)
    
    return update


def show_summary(stats: Dict[str, Any]) -> None:
    """显示处理摘要
    
    Args:
        stats: 统计数据
    """
    print_header("处理完成")
    console.print(f"总文件数: {stats.get('total', 0)}")
    console.print(f"成功: [green]{stats.get('success', 0)}[/]")
    console.print(f"失败: [red]{stats.get('failed', 0)}[/]")
    console.print(f"跳过: [yellow]{stats.get('skipped', 0)}[/]")
    
    if stats.get('failed', 0) > 0 and 'failed_files' in stats:
        console.print("\n失败的文件:")
        for file in stats['failed_files']:
            console.print(f"  [red]{file}[/]")


def interactive_setup() -> Dict[str, Any]:
    """交互式设置
    
    Returns:
        Dict[str, Any]: 设置参数
    """
    print_header("欢迎使用 Prompt Factory")
    
    # 收集API密钥
    api_keys = collect_api_keys()
    if not api_keys:
        print_error("未提供任何API密钥，程序无法继续")
        return {}
    
    # 选择服务提供商
    provider = select_provider(api_keys)
    if not provider:
        return {}
    
    # 返回设置参数
    return {
        "api_keys": api_keys,
        "provider": provider,
        "api_key": api_keys[provider]
    }