"""模板管理模块

提供模板加载、验证和管理的功能。
"""

import os
import glob
from typing import Dict, List, Optional


class TemplateManager:
    """模板管理器，负责加载和验证系统提示模板。
    """
    def __init__(self, templates_dir: str = None):
        """初始化模板管理器
        
        Args:
            templates_dir: 模板目录路径，默认为项目根目录的templates文件夹
        """
        if templates_dir is None:
            # 使用相对路径，确保在项目中的任何位置都能正确找到模板目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.templates_dir = os.path.join(base_dir, "templates")
        else:
            self.templates_dir = templates_dir
            
        # 确保模板目录存在
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # 缓存已加载的模板
        self._templates_cache: Dict[str, str] = {}
        
        # 当前激活的模板名称
        self.active_template: Optional[str] = None
    
    def list_templates(self) -> List[str]:
        """获取可用模板列表（get_available_templates的别名）
        
        Returns:
            List[str]: 模板名称列表
        """
        return self.get_available_templates()
    
    def get_available_templates(self) -> List[str]:
        """获取可用模板列表
        
        Returns:
            List[str]: 模板名称列表
        """
        template_files = glob.glob(os.path.join(self.templates_dir, "*.txt"))
        return [os.path.basename(f).replace(".txt", "") for f in template_files]
    
    def load_template(self, template_name: str = "standard") -> Optional[str]:
        """加载指定模板
        
        Args:
            template_name: 模板名称，默认为standard
            
        Returns:
            Optional[str]: 模板内容，不存在则返回None
        """
        # 验证模板名称格式
        if not template_name or not isinstance(template_name, str):
            return None
            
        # 检查缓存
        if template_name in self._templates_cache:
            self.active_template = template_name
            return self._templates_cache[template_name]
        
        # 构建模板文件路径
        template_path = os.path.join(self.templates_dir, f"{template_name}.txt")
        
        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            return None
        
        try:
            # 读取模板文件
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
                
            # 缓存模板内容
            self._templates_cache[template_name] = template_content
            
            # 设置当前激活的模板
            self.active_template = template_name
            
            return template_content
            
        except Exception as e:
            return None
    
    def get_current_template(self) -> Optional[str]:
        """获取当前激活的模板内容
        
        Returns:
            Optional[str]: 当前模板内容，如果没有激活的模板则返回None
        """
        if not self.active_template:
            return None
            
        return self._templates_cache.get(self.active_template)
        
    def validate_template(self, template_content: str) -> bool:
        """验证模板内容是否有效
        
        Args:
            template_content: 模板内容
            
        Returns:
            bool: 模板是否有效
        """
        # 检查模板是否包含系统消息和用户消息部分
        if "## System Message" not in template_content:
            return False
            
        if "## User Message" not in template_content:
            return False
            
        # 检查模板是否包含{PROMPT}占位符
        if "{PROMPT}" not in template_content:
            return False
            
        return True