"""环境管理模块

提供环境检查、依赖安装和配置验证功能。
"""

import os
import sys
import logging
import subprocess
import importlib.util
from typing import Dict, List, Tuple, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('environment')

# 依赖包列表
REQUIRED_PACKAGES = [
    "requests",  # API请求
    "rich",      # 终端输出美化
]

# 可选依赖包列表（用于API服务器等扩展功能）
OPTIONAL_PACKAGES = {
    "api_server": ["flask", "flask-cors"],
}


def check_python_version() -> bool:
    """检查Python版本
    
    Returns:
        bool: 版本是否满足要求
    """
    MIN_PYTHON_VERSION = (3, 7)
    current_version = sys.version_info
    
    if current_version.major < MIN_PYTHON_VERSION[0] or \
       (current_version.major == MIN_PYTHON_VERSION[0] and 
        current_version.minor < MIN_PYTHON_VERSION[1]):
        logger.error(f"Python版本不满足要求: 当前版本 {current_version.major}.{current_version.minor}, "
                     f"最低要求 {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}")
        return False
        
    return True


def check_dependencies(including_optional: bool = False) -> Tuple[bool, List[str]]:
    """检查依赖包是否已安装
    
    Args:
        including_optional: 是否包括可选依赖包
        
    Returns:
        Tuple[bool, List[str]]: (是否全部已安装, 缺失的包列表)
    """
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if including_optional:
        for category, packages in OPTIONAL_PACKAGES.items():
            for package in packages:
                if importlib.util.find_spec(package) is None:
                    missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages


def install_dependencies(packages: List[str]) -> bool:
    """安装依赖包
    
    Args:
        packages: 需要安装的包列表
        
    Returns:
        bool: 安装是否成功
    """
    if not packages:
        return True
        
    try:
        logger.info(f"开始安装依赖包: {', '.join(packages)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"安装依赖包时出错: {e}")
        return False


def validate_api_key(api_key: str, provider: str = "anthropic") -> bool:
    """验证API密钥是否有效（发送一个简单请求）
    
    Args:
        api_key: API密钥
        provider: 服务提供商，默认为anthropic
        
    Returns:
        bool: 密钥是否有效
    """
    try:
        import requests
        
        # 根据提供商选择验证端点和方法
        if provider == "anthropic":
            headers = {
                "x-api-key": api_key,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json={
                    "model": "claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )
        elif provider == "openai":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )
        elif provider == "openrouter":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "anthropic/claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )
        else:
            logger.error(f"不支持的服务提供商: {provider}")
            return False
            
        if response.status_code == 200:
            return True
        else:
            logger.error(f"API密钥验证失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"验证API密钥时出错: {e}")
        return False


def setup_environment(force_install: bool = False, auto_fix: bool = True) -> Tuple[bool, Dict[str, Any]]:
    """设置运行环境
    
    Args:
        force_install: 是否强制安装依赖包
        auto_fix: 是否自动修复问题
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (设置是否成功, 环境信息字典)
    """
    env_info = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "directories": {},
        "dependencies": {"required": {}, "optional": {}}
    }
    
    # 检查Python版本
    python_version_ok = check_python_version()
    env_info["python_version_ok"] = python_version_ok
    if not python_version_ok and not auto_fix:
        return False, env_info
    
    # 检查依赖包
    all_installed, missing_packages = check_dependencies()
    env_info["dependencies"]["required"]["all_installed"] = all_installed
    env_info["dependencies"]["required"]["missing"] = missing_packages
    
    # 检查可选依赖包
    optional_installed, optional_missing = check_dependencies(including_optional=True)
    env_info["dependencies"]["optional"]["all_installed"] = optional_installed
    env_info["dependencies"]["optional"]["missing"] = list(set(optional_missing) - set(missing_packages))
    
    # 如果有缺失的必需包，尝试安装
    if (not all_installed or force_install) and auto_fix:
        logger.info("开始安装缺失的依赖包...")
        if not install_dependencies(missing_packages):
            return False, env_info
        env_info["dependencies"]["required"]["all_installed"] = True
        env_info["dependencies"]["required"]["missing"] = []
    
    # 创建必要的目录
    try:
        # 获取项目根目录
        current_file = os.path.abspath(__file__)
        src_dir = os.path.dirname(os.path.dirname(current_file))
        project_root = os.path.dirname(src_dir)
        env_info["project_root"] = project_root
        
        # 创建输出目录
        output_dir = os.path.join(project_root, 'output')
        os.makedirs(output_dir, exist_ok=True)
        env_info["directories"]["output"] = output_dir
        
        # 创建日志目录
        log_dir = os.path.join(project_root, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        env_info["directories"]["logs"] = log_dir
        
        # 创建缓存目录
        cache_dir = os.path.join(project_root, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        env_info["directories"]["cache"] = cache_dir
        
        # 设置日志处理器
        root_logger = logging.getLogger()
        log_handler = create_secure_log_handler(log_dir)
        root_logger.addHandler(log_handler)
        
        # 注册程序退出时的清理函数
        import atexit
        atexit.register(clear_sensitive_data)
        
        # 设置成功
        env_info["setup_success"] = True
        return True, env_info
        
    except Exception as e:
        logger.error(f"创建目录时出错: {e}")
        env_info["setup_error"] = str(e)
        env_info["setup_success"] = False
        return False, env_info


def create_secure_log_handler(log_dir: str) -> logging.Handler:
    """创建安全的日志处理器，避免记录敏感信息
    
    Args:
        log_dir: 日志目录路径
        
    Returns:
        logging.Handler: 日志处理器
    """
    import datetime
    import logging.handlers
    
    # 创建日志文件名
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f"prompt_factory_{date_str}.log")
    
    # 创建文件处理器
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    
    # 设置格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    return file_handler


def sanitize_log_message(message: str, sensitive_values: List[str]) -> str:
    """清理日志消息中的敏感信息
    
    Args:
        message: 原始日志消息
        sensitive_values: 敏感信息列表，如API密钥等
        
    Returns:
        str: 清理后的日志消息
    """
    result = message
    for value in sensitive_values:
        if value and len(value) > 8 and value in result:
            # 用星号替换中间部分，保留前后各3个字符
            masked = value[:3] + "*" * (len(value) - 6) + value[-3:]
            result = result.replace(value, masked)
    return result


def clear_sensitive_data():
    """清理内存中的敏感数据
    
    程序退出前调用此函数清理内存中的敏感数据。
    """
    import gc
    
    # 强制进行垃圾回收
    gc.collect()
    
    # 重置环境变量
    if "OPENAI_API_KEY" in os.environ:
        os.environ["OPENAI_API_KEY"] = ""
    if "ANTHROPIC_API_KEY" in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = ""
    if "OPENROUTER_API_KEY" in os.environ:
        os.environ["OPENROUTER_API_KEY"] = ""