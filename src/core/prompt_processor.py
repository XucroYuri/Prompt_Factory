"""提示词处理模块

提供提示词的加载、处理和生成的功能。
"""

import os
import json
import requests
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from .template_manager import TemplateManager
from .model_manager import ModelManager

# 设置日志
logger = logging.getLogger('prompt_processor')


class ProcessingError(Exception):
    """提示词处理异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class PromptProcessor:
    """提示词处理器，负责处理和生成提示词。"""
    
    def __init__(self, api_key: str, template_name: str = "standard", 
                 model: str = "anthropic/claude-3.7-sonnet", temperature: float = 0.7, 
                 model_manager: Optional[ModelManager] = None,
                 output_path: Optional[str] = None, timeout: int = 60, max_retries: int = 5,
                 retry_interval: int = 3, file_extensions: Optional[List[str]] = None):
        """初始化提示词处理器
        
        Args:
            api_key: API密钥
            template_name: 模板名称，默认standard
            model: 使用模型，默认anthropic/claude-3.7-sonnet
            temperature: 输出随机性
            model_manager: 模型管理器实例（可选）
            output_path: 输出路径（可选），指定结果保存的绝对路径，默认为项目根目录下的output目录
            timeout: API请求超时时间（秒），默认30秒
            max_retries: API请求失败后的最大重试次数，默认2次
            file_extensions: 支持处理的文件扩展名列表，默认为None表示处理所有文件
        
        Raises:
            ProcessingError: 初始化失败
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.file_extensions = file_extensions
        
        # 设置输出路径，如果未提供则使用默认output目录
        if output_path:
            self.output_path = output_path
        else:
            # 获取项目根目录的output文件夹路径
            current_file = os.path.abspath(__file__)
            src_dir = os.path.dirname(os.path.dirname(current_file))
            project_root = os.path.dirname(src_dir)
            self.output_path = os.path.join(project_root, 'output')
        
        # 初始化模板管理器
        self.template_manager = TemplateManager()
        
        # 加载指定的模板
        self.system_template = self.template_manager.load_template(template_name)
        if not self.system_template:
            # 如果指定模板加载失败，尝试加载标准模板
            self.system_template = self.template_manager.load_template("standard")
            if not self.system_template:
                raise ProcessingError("无法加载系统提示模板")
        
        # 初始化或使用已有的模型管理器
        self.model_manager = model_manager or ModelManager()
    
    def process_file(self, file_path: str) -> bool:
        """处理单个文件
        
        Args:
            file_path: 需要处理的文件路径
            
        Returns:
            bool: 处理是否成功
            
        Raises:
            ProcessingError: 处理文件时出错
        """
        try:
            if not os.path.exists(file_path):
                raise ProcessingError(f"文件不存在: {file_path}")
                
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 处理内容
            result = self.process_content(content)
            
            if not result:
                return False
                
            # 保存处理结果
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result)
                
            return True
            
        except Exception as e:
            raise ProcessingError(f"处理文件 {file_path} 时出错", {"original_error": str(e)})
    
    def process_content(self, content: str) -> Optional[str]:
        """处理文本内容
        
        Args:
            content: 需要处理的文本内容
            
        Returns:
            Optional[str]: 处理后的内容，失败则返回None
            
        Raises:
            ProcessingError: 处理内容时出错
        """
        try:
            # 获取系统消息和用户消息
            system_msg, user_msg = self._extract_messages_from_template()
            
            # 替换占位符
            user_msg = user_msg.replace("{PROMPT}", content)
            
            # 调用模型API获取响应
            response = self._call_model_api(system_msg, user_msg)
            
            return response
            
        except Exception as e:
            raise ProcessingError("处理内容时出错", {"original_error": str(e)})
    
    def _extract_messages_from_template(self) -> Tuple[str, str]:
        """从模板中提取系统消息和用户消息
        
        Returns:
            Tuple[str, str]: (系统消息, 用户消息)
            
        Raises:
            ProcessingError: 提取消息时出错
        """
        try:
            # 确保模板有效
            if not self.system_template:
                raise ProcessingError("未加载有效的系统提示模板")
                
            # 分割模板以提取系统消息和用户消息
            system_msg = ""
            user_msg = ""
            
            parts = self.system_template.split("## System Message")
            if len(parts) > 1:
                system_part = parts[1].split("## User Message")
                if len(system_part) > 0:
                    system_msg = system_part[0].strip()
                    
            parts = self.system_template.split("## User Message")
            if len(parts) > 1:
                user_msg = parts[1].strip()
                
            if not system_msg or not user_msg:
                raise ProcessingError("无法从模板中提取系统消息和用户消息")
                
            return system_msg, user_msg
            
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise e
            raise ProcessingError("从模板中提取消息时出错", {"original_error": str(e)})
    
    def _call_model_api(self, system_msg: str, user_msg: str) -> str:
        """调用模型API获取响应
        
        Args:
            system_msg: 系统消息
            user_msg: 用户消息
            
        Returns:
            str: 模型响应
            
        Raises:
            ProcessingError: 调用API时出错
        """
        try:
            # 解析模型ID
            provider_id, model_name = self.model_manager.parse_model_id(self.model)
            
            # 根据不同的服务提供商构建对应的请求
            if provider_id == "openai":
                return self._call_openai_api(system_msg, user_msg, model_name)
            elif provider_id == "openrouter":
                return self._call_openrouter_api(system_msg, user_msg, model_name)
            elif provider_id == "deepseek":
                return self._call_deepseek_api(system_msg, user_msg, model_name)
            else:
                raise ProcessingError(f"不支持的服务提供商: {provider_id}，请使用 'openai'、'openrouter' 或 'deepseek'")
                
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise e
            raise ProcessingError("调用模型API时出错", {"original_error": str(e)})
    
    def _call_openai_api(self, system_msg: str, user_msg: str, model_name: str) -> str:
        """调用OpenAI API
        
        Args:
            system_msg: 系统消息
            user_msg: 用户消息
            model_name: 模型名称
            
        Returns:
            str: API响应
            
        Raises:
            ProcessingError: 调用API时出错
        """
        current_retry = 0
        while current_retry <= self.max_retries:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": self.temperature
                }
                
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    error_msg = f"OpenAI API返回错误: {response.status_code} / OpenAI API returned error: {response.status_code}"
                    
                    # 检查是否需要重试（对于429、500、502、503、504等错误）
                    if response.status_code in [429, 500, 502, 503, 504] and current_retry < self.max_retries:
                        current_retry += 1
                        # 指数退避策略，每次重试等待时间翻倍
                        wait_time = self.retry_interval * (2 ** current_retry)
                        wait_time = min(wait_time, 60)  # 限制最大等待时间为60秒
                        logger.info(f"OpenAI API返回错误码{response.status_code}，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                        
                    raise ProcessingError(
                        error_msg, 
                        {"response": response.text}
                    )
                    
                result = response.json()
                # 记录成功响应的请求ID和响应信息
                logger.info(f"DeepSeek API请求成功 [{request_id}]: 模型={model_name}")
                
                # 添加调试信息，如响应token数量等
                try:
                    usage_info = result.get("usage", {})
                    if usage_info:
                        logger.debug(f"DeepSeek API请求完成 [{request_id}]: 输入tokens={usage_info.get('prompt_tokens', 'N/A')}, 输出tokens={usage_info.get('completion_tokens', 'N/A')}")
                except Exception as usage_err:
                    logger.debug(f"无法获取使用信息 [{request_id}]: {str(usage_err)}")
                
                return result["choices"][0]["message"]["content"]
        
            except requests.exceptions.Timeout:
                error_msg = f"调用OpenAI API超时 / OpenAI API request timeout"
                if current_retry < self.max_retries:
                    current_retry += 1
                    # 超时情况下也使用指数退避策略
                    wait_time = self.retry_interval * (2 ** current_retry)
                    wait_time = min(wait_time, 30)  # 限制最大等待时间为30秒
                    logger.info(f"OpenAI API请求超时，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                raise ProcessingError(error_msg, {"timeout": f"{self.timeout}秒"})
            except requests.exceptions.ConnectionError:
                error_msg = f"调用OpenAI API连接错误 / OpenAI API connection error"
                if current_retry < self.max_retries:
                    current_retry += 1
                    # 使用指数退避策略，每次重试等待时间翻倍
                    wait_time = self.retry_interval * (2 ** current_retry)
                    # 限制最大等待时间为60秒
                    wait_time = min(wait_time, 60)
                    logger.info(f"连接OpenAI API失败，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                raise ProcessingError(error_msg, {"suggestion": "请检查网络连接或API服务状态 / Please check your network connection or API service status"})
            except Exception as e:
                if isinstance(e, ProcessingError):
                    raise e
                error_msg = f"调用OpenAI API时出错 / Error calling OpenAI API"
                raise ProcessingError(error_msg, {"original_error": str(e)})
            
            # 如果执行到这里，说明请求成功，跳出重试循环
            break
    
    def _call_openrouter_api(self, system_msg: str, user_msg: str, model_name: str) -> str:
        """调用OpenRouter API
        
        Args:
            system_msg: 系统消息
            user_msg: 用户消息
            model_name: 模型名称
            
        Returns:
            str: API响应
            
        Raises:
            ProcessingError: 调用API时出错
        """
        current_retry = 0
        while current_retry <= self.max_retries:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": self.temperature
                }
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    error_msg = f"OpenRouter API返回错误: {response.status_code} / OpenRouter API returned error: {response.status_code}"
                    
                    # 检查是否需要重试（对于429、500、502、503、504等错误）
                    if response.status_code in [429, 500, 502, 503, 504] and current_retry < self.max_retries:
                        current_retry += 1
                        # 指数退避策略，每次重试等待时间翻倍
                        wait_time = self.retry_interval * (2 ** current_retry)
                        wait_time = min(wait_time, 60)  # 限制最大等待时间为60秒
                        logger.info(f"OpenRouter API返回错误码{response.status_code}，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                        
                    raise ProcessingError(
                        error_msg, 
                        {"response": response.text}
                    )
                    
                result = response.json()
                # 记录成功响应的请求ID和响应信息
                logger.info(f"DeepSeek API请求成功 [{request_id}]: 模型={model_name}")
                
                # 添加调试信息，如响应token数量等
                try:
                    usage_info = result.get("usage", {})
                    if usage_info:
                        logger.debug(f"DeepSeek API请求完成 [{request_id}]: 输入tokens={usage_info.get('prompt_tokens', 'N/A')}, 输出tokens={usage_info.get('completion_tokens', 'N/A')}")
                except Exception as usage_err:
                    logger.debug(f"无法获取使用信息 [{request_id}]: {str(usage_err)}")
                
                return result["choices"][0]["message"]["content"]
            
            except requests.exceptions.Timeout:
                error_msg = f"调用OpenRouter API超时 / OpenRouter API request timeout"
                if current_retry < self.max_retries:
                    current_retry += 1
                    # 超时情况下也使用指数退避策略
                    wait_time = self.retry_interval * (2 ** current_retry)
                    wait_time = min(wait_time, 30)  # 限制最大等待时间为30秒
                    logger.info(f"OpenRouter API请求超时，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                raise ProcessingError(error_msg, {"timeout": f"{self.timeout}秒"})
            except requests.exceptions.ConnectionError:
                error_msg = f"调用OpenRouter API连接错误 / OpenRouter API connection error"
                if current_retry < self.max_retries:
                    current_retry += 1
                    # 使用指数退避策略，每次重试等待时间翻倍
                    wait_time = self.retry_interval * (2 ** current_retry)
                    # 限制最大等待时间为60秒
                    wait_time = min(wait_time, 60)
                    logger.info(f"连接OpenRouter API失败，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                raise ProcessingError(error_msg, {"suggestion": "请检查网络连接或API服务状态 / Please check your network connection or API service status"})
            except Exception as e:
                if isinstance(e, ProcessingError):
                    raise e
                error_msg = f"调用OpenRouter API时出错 / Error calling OpenRouter API"
                raise ProcessingError(error_msg, {"original_error": str(e)})
                
                # 如果执行到这里，说明请求成功，跳出重试循环
                break
            
    def _call_deepseek_api(self, system_msg: str, user_msg: str, model_name: str) -> str:
        """调用DeepSeek API
        
        Args:
            system_msg: 系统消息
            user_msg: 用户消息
            model_name: 模型名称
            
        Returns:
            str: API响应
            
        Raises:
            ProcessingError: 调用API时出错
        """
        current_retry = 0
        while current_retry <= self.max_retries:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": self.temperature
                }
                
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                # 为每个请求生成唯一标识符
                request_id = f"req-{int(time.time())}-{hash(str(data)) % 10000:04d}"
                
                # 记录请求信息
                logger.debug(f"DeepSeek API请求开始 [{request_id}]: 模型={model_name}")
                
                if response.status_code != 200:
                    # 详细分析HTTP错误类型
                    error_details = {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response": response.text
                    }
                    
                    # 根据状态码分类处理
                    if response.status_code == 400:
                        error_type = "请求无效 / Bad Request"
                        error_details["error_type"] = "bad_request"
                        error_details["suggestion"] = "请求参数有误，请检查请求格式 / Invalid request parameters, please check request format"
                    elif response.status_code == 401:
                        error_type = "身份验证失败 / Unauthorized"
                        error_details["error_type"] = "unauthorized"
                        error_details["suggestion"] = "API密钥无效或已过期，请检查API密钥 / Invalid or expired API key, please check your API key"
                    elif response.status_code == 403:
                        error_type = "权限不足 / Forbidden"
                        error_details["error_type"] = "forbidden"
                        error_details["suggestion"] = "没有足够的权限访问该资源，请检查账户权限 / Insufficient permission to access the resource, please check account permissions"
                    elif response.status_code == 404:
                        error_type = "资源不存在 / Not Found"
                        error_details["error_type"] = "not_found"
                        error_details["suggestion"] = "请求的资源不存在，请检查API端点或模型名称 / Requested resource not found, please check API endpoint or model name"
                    elif response.status_code == 429:
                        error_type = "请求过多 / Too Many Requests"
                        error_details["error_type"] = "rate_limited"
                        error_details["suggestion"] = "已超出API速率限制，请降低请求频率或提高账户等级 / API rate limit exceeded, please reduce request frequency or upgrade account"
                    elif response.status_code == 500:
                        error_type = "服务器内部错误 / Internal Server Error"
                        error_details["error_type"] = "server_error"
                        error_details["suggestion"] = "DeepSeek服务器内部错误，请稍后重试 / DeepSeek server internal error, please try again later"
                    elif response.status_code in [502, 503, 504]:
                        error_type = "服务不可用 / Service Unavailable"
                        error_details["error_type"] = "service_unavailable"
                        error_details["suggestion"] = "DeepSeek服务暂时不可用，请稍后重试 / DeepSeek service temporarily unavailable, please try again later"
                    else:
                        error_type = f"未知HTTP错误 / Unknown HTTP Error: {response.status_code}"
                        error_details["error_type"] = "unknown_http_error"
                        error_details["suggestion"] = "发生未知HTTP错误，请联系DeepSeek支持 / Unknown HTTP error occurred, please contact DeepSeek support"
                    
                    error_msg = f"DeepSeek API {error_type} / DeepSeek API {error_type}"
                    
                    # 记录详细错误日志
                    logger.error(f"DeepSeek API请求失败 [{request_id}]: {error_type} - 状态码: {response.status_code}")
                    
                    # 尝试解析响应内容
                    try:
                        error_json = response.json()
                        if 'error' in error_json:
                            error_details["api_error"] = error_json['error']
                    except Exception as json_err:
                        error_details["response_parse_error"] = str(json_err)
                    
                    # 检查是否需要重试（对于429、500、502、503、504等错误）
                    if response.status_code in [429, 500, 502, 503, 504] and current_retry < self.max_retries:
                        current_retry += 1
                        # 指数退避策略，每次重试等待时间翻倍
                        wait_time = self.retry_interval * (2 ** current_retry)
                        wait_time = min(wait_time, 60)  # 限制最大等待时间为60秒
                        logger.info(f"DeepSeek API返回错误码 [{request_id}] {response.status_code}，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                        time.sleep(wait_time)
                        continue
                        
                    raise ProcessingError(error_msg, error_details)
                    
                result = response.json()
                # 记录成功响应的请求ID和响应信息
                logger.info(f"DeepSeek API请求成功 [{request_id}]: 模型={model_name}")
                
                # 添加调试信息，如响应token数量等
                try:
                    usage_info = result.get("usage", {})
                    if usage_info:
                        logger.debug(f"DeepSeek API请求完成 [{request_id}]: 输入tokens={usage_info.get('prompt_tokens', 'N/A')}, 输出tokens={usage_info.get('completion_tokens', 'N/A')}")
                except Exception as usage_err:
                    logger.debug(f"无法获取使用信息 [{request_id}]: {str(usage_err)}")
                
                return result["choices"][0]["message"]["content"]
                
            except requests.exceptions.Timeout as timeout_err:
                # 为每次请求生成唯一标识符，便于跟踪
                request_id = f"req-{int(time.time())}-{hash(str(timeout_err)) % 10000:04d}"
                
                # 详细分析超时类型
                error_details = {
                    "request_id": request_id,
                    "timeout_value": f"{self.timeout}秒",
                    "original_error": str(timeout_err)
                }
                
                # 检测超时原因
                if "read timeout" in str(timeout_err):
                    error_type = "读取超时 / Read Timeout"
                    error_details["error_type"] = "read_timeout"
                    error_details["suggestion"] = "服务器响应时间过长，请稍后重试或增加超时设置 / Server response time too long, please try again later or increase timeout setting"
                elif "connect timeout" in str(timeout_err):
                    error_type = "连接超时 / Connect Timeout"
                    error_details["error_type"] = "connect_timeout"
                    error_details["suggestion"] = "无法连接到服务器，请检查网络连接或服务器状态 / Cannot connect to server, please check network connection or server status"
                else:
                    error_type = "请求超时 / Request Timeout"
                    error_details["error_type"] = "general_timeout"
                    error_details["suggestion"] = "请求处理超时，请检查网络状况或稍后重试 / Request processing timed out, please check network condition or try again later"
                
                # 记录详细错误日志
                logger.error(f"DeepSeek API {error_type} [{request_id}]: {str(timeout_err)}")
                
                error_msg = f"调用DeepSeek API {error_type} / DeepSeek API {error_type}"
                
                if current_retry < self.max_retries:
                    current_retry += 1
                    # 超时情况下也使用指数退避策略
                    wait_time = self.retry_interval * (2 ** current_retry)
                    wait_time = min(wait_time, 30) # 限制最大等待时间为30秒
                    logger.info(f"DeepSeek API请求超时 [{request_id}]，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                raise ProcessingError(error_msg, error_details)
            except requests.exceptions.ConnectionError as conn_err:
                # 为每次请求生成唯一标识符，便于跟踪
                request_id = f"req-{int(time.time())}-{hash(str(conn_err)) % 10000:04d}"
                
                # 详细分析连接错误类型
                error_details = {"request_id": request_id}
                
                # 根据错误类型细分错误信息
                if "getaddrinfo failed" in str(conn_err) or "Name or service not known" in str(conn_err):
                    error_type = "DNS解析失败 / DNS Resolution Failed"
                    error_details["error_type"] = "dns_error"
                    error_details["suggestion"] = "请检查网络DNS设置或域名是否正确 / Please check your DNS settings or domain name"
                elif "Connection refused" in str(conn_err):
                    error_type = "连接被拒绝 / Connection Refused"
                    error_details["error_type"] = "connection_refused"
                    error_details["suggestion"] = "目标服务器拒绝连接，请检查服务是否可用 / Target server refused connection, please check if service is available"
                elif "SSLError" in str(conn_err) or "SSL" in str(conn_err):
                    error_type = "SSL证书错误 / SSL Certificate Error"
                    error_details["error_type"] = "ssl_error"
                    error_details["suggestion"] = "SSL连接异常，可能是证书问题 / SSL connection issue, possibly certificate related"
                elif "Timeout" in str(conn_err) or "timed out" in str(conn_err):
                    error_type = "连接超时 / Connection Timeout"
                    error_details["error_type"] = "connection_timeout"
                    error_details["suggestion"] = "连接超时，请检查网络速度或服务器响应时间 / Connection timed out, please check network speed or server response time"
                elif "Proxy" in str(conn_err):
                    error_type = "代理错误 / Proxy Error"
                    error_details["error_type"] = "proxy_error"
                    error_details["suggestion"] = "代理服务器连接异常，请检查代理设置 / Proxy connection error, please check proxy settings"
                else:
                    error_type = "网络连接错误 / Network Connection Error"
                    error_details["error_type"] = "general_connection_error"
                    error_details["suggestion"] = "请检查网络连接状态 / Please check your network connection status"
                
                # 添加错误原始信息
                error_details["original_error"] = str(conn_err)
                
                # 添加网络诊断信息
                import socket
                try:
                    # 尝试获取本地主机名和IP地址
                    hostname = socket.gethostname()
                    local_ip = socket.gethostbyname(hostname)
                    error_details["network_info"] = {
                        "hostname": hostname,
                        "local_ip": local_ip
                    }
                    
                    # 尝试解析API域名
                    try:
                        api_ip = socket.gethostbyname("api.deepseek.com")
                        error_details["network_info"]["api_dns_resolved"] = True
                        error_details["network_info"]["api_ip"] = api_ip
                    except socket.gaierror:
                        error_details["network_info"]["api_dns_resolved"] = False
                except Exception as net_diag_err:
                    error_details["network_diagnostics_error"] = str(net_diag_err)
                
                error_msg = f"调用DeepSeek API {error_type} / DeepSeek API {error_type}"
                
                # 记录详细错误日志
                logger.error(f"DeepSeek API请求失败 [{request_id}]: {error_type} - {str(conn_err)}")
                
                if current_retry < self.max_retries:
                    current_retry += 1
                    # 使用指数退避策略，每次重试等待时间翻倍
                    wait_time = self.retry_interval * (2 ** current_retry)
                    # 限制最大等待时间为60秒
                    wait_time = min(wait_time, 60)
                    logger.info(f"连接DeepSeek API失败 [{request_id}]，{wait_time}秒后重试 ({current_retry}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                    
                raise ProcessingError(error_msg, error_details)
            except Exception as e:
                # 为异常生成唯一标识符
                request_id = f"req-{int(time.time())}-{hash(str(e)) % 10000:04d}"
                
                if isinstance(e, ProcessingError):
                    raise e
                    
                # 详细的异常信息收集
                error_details = {
                    "request_id": request_id,
                    "original_error": str(e),
                    "error_type": type(e).__name__
                }
                
                # 尝试获取更多错误上下文
                import traceback
                error_details["traceback"] = traceback.format_exc().split("\n")[-10:]
                
                # 添加请求信息
                try:
                    error_details["request_info"] = {
                        "model": model_name,
                        "temperature": self.temperature,
                        "timeout": self.timeout
                    }
                except Exception as info_err:
                    error_details["info_error"] = str(info_err)
                
                # 记录详细错误日志
                logger.error(f"DeepSeek API未预期异常 [{request_id}]: {type(e).__name__} - {str(e)}")
                
                error_msg = f"调用DeepSeek API时出错: {type(e).__name__} / Error calling DeepSeek API: {type(e).__name__}"
                raise ProcessingError(error_msg, error_details)
            
            # 如果执行到这里，说明请求成功，跳出重试循环
            break
    
    def set_template(self, template_name: str) -> bool:
        """设置模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            bool: 是否成功更改模板
        """
        template_content = self.template_manager.load_template(template_name)
        if template_content:
            self.system_template = template_content
            return True
        return False
    
    def get_active_template(self) -> str:
        """获取当前模板名称
        
        Returns:
            str: 当前模板名称
        """
        return self.template_manager.active_template or ""
    
    def process_directory(self, directory_path: str, file_extensions: List[str] = None, recursive: bool = True, callbacks: Dict[str, Callable] = None) -> Dict[str, Any]:
        """处理目录
        
        Args:
            directory_path: 目录路径
            file_extensions: 要处理的文件扩展名列表，默认为['.md']，None表示处理所有文件
            recursive: 是否递归处理子目录，默认为True
            callbacks: 回调函数字典，可包含以下键：
                - file_processed: 文件处理完成时的回调，参数为(file_path, success)
                - file_skipped: 文件被跳过时的回调，参数为(file_path)
                - directory_entered: 进入目录时的回调，参数为(dir_path)
            
        Returns:
            Dict[str, Any]: 处理统计结果字典
            
        Raises:
            ProcessingError: 处理目录时出错
        """
        # 标准化目录路径，确保在不同操作系统下都能正确处理
        directory_path = os.path.normpath(directory_path)
        
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            raise ProcessingError(f"目录不存在: {directory_path}")
        
        # 设置默认文件扩展名
        if file_extensions is None:
            file_extensions = ['.md']
        elif len(file_extensions) == 0:
            # 空列表表示处理所有文件
            file_extensions = None
            
        # 保存文件扩展名，供外部访问
        self.file_extensions = file_extensions
            
        # 创建基于日期和批次号的输出目录
        import datetime
        import string
        import random
        from pathlib import Path
        
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        batch_id = random.choice(string.ascii_uppercase) + ''.join(random.choices('0123456789', k=3))
        output_dir_name = f"{date_str}-{batch_id}"
        
        # 确保输出目录存在
        output_base_dir = os.path.join(self.output_path, output_dir_name)
        os.makedirs(output_base_dir, exist_ok=True)
        
        # 记录开始时间
        start_time = time.time()
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "failed_files": [],
            "output_dir": output_base_dir,
            "start_time": start_time,
            "end_time": None,
            "elapsed_time": None
        }
        
        # 处理文件的函数
        def process_file(file_path: str, rel_dir: str) -> None:
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # 检查文件扩展名是否需要处理
            if file_extensions is not None and file_ext not in file_extensions:
                stats["skipped"] += 1
                # 调用文件跳过回调
                if callbacks and "file_skipped" in callbacks:
                    callbacks["file_skipped"](file_path)
                return
                
            # 跳过已优化的文件
            if "_optimized" in file_name:
                stats["skipped"] += 1
                # 调用文件跳过回调
                if callbacks and "file_skipped" in callbacks:
                    callbacks["file_skipped"](file_path)
                return
                
            stats["total"] += 1
            
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 处理内容
                result = self.process_content(content)
                
                if not result:
                    stats["failed"] += 1
                    stats["failed_files"].append(file_path)
                    # 调用文件处理回调（失败）
                    if callbacks and "file_processed" in callbacks:
                        callbacks["file_processed"](file_path, False)
                    return
                
                # 创建相应的输出目录
                output_dir = os.path.join(output_base_dir, rel_dir)
                os.makedirs(output_dir, exist_ok=True)
                
                # 保存优化后的内容
                output_file_path = os.path.join(output_dir, file_name)
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                stats["success"] += 1
                
                # 调用文件处理回调（成功）
                if callbacks and "file_processed" in callbacks:
                    callbacks["file_processed"](file_path, True)
                
            except Exception as e:
                stats["failed"] += 1
                stats["failed_files"].append(file_path)
                logger.error(f"处理文件 {file_path} 时出错: {e}")
                # 记录错误但继续处理其他文件
                # 如果是ProcessingError异常，保留详细信息但不中断程序
                if isinstance(e, ProcessingError) and hasattr(e, 'details'):
                    logger.error(f"错误详情: {e.details}")
                
                # 调用文件处理回调（失败）
                if callbacks and "file_processed" in callbacks:
                    callbacks["file_processed"](file_path, False)
        
        # 开始处理文件
        if recursive:
            # 递归处理目录
            for root, _, files in os.walk(directory_path):
                # 计算相对路径，用于保持目录结构
                rel_path = os.path.relpath(root, directory_path)
                
                # 调用进入目录回调
                if callbacks and "directory_entered" in callbacks:
                    callbacks["directory_entered"](root)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    process_file(file_path, rel_path)
        else:
            # 只处理顶层目录
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isfile(item_path):
                    process_file(item_path, "")
        
        # 记录结束时间和总用时
        end_time = time.time()
        stats["end_time"] = end_time
        stats["elapsed_time"] = end_time - start_time
        
        # 记录处理统计到日志
        logger.info(f"处理完成: 共 {stats['total']} 个文件, 成功 {stats['success']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}")
        logger.info(f"输出目录: {output_base_dir}")
        logger.info(f"处理用时: {stats['elapsed_time']:.2f} 秒")

        return stats