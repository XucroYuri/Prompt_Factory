"""任务状态管理模块

提供任务进度跟踪、中断恢复和报告生成功能。
"""

import os
import json
import time
import logging
import datetime
from typing import Dict, List, Any, Optional, Callable
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('task_manager')

# 创建Rich控制台对象
console = Console()


class TaskState:
    """任务状态类，用于跟踪和恢复任务进度"""
    
    def __init__(self, task_id: str, input_path: str, output_path: str):
        """初始化任务状态
        
        Args:
            task_id: 任务ID
            input_path: 输入路径
            output_path: 输出路径
        """
        self.task_id = task_id
        self.input_path = input_path
        self.output_path = output_path
        self.start_time = time.time()
        self.end_time = None
        self.status = "running"  # running, paused, completed, failed
        self.stats = {
            "total": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "failed_files": [],
            "processed_files": []
        }
        self.current_file = None
        self.last_update = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """将任务状态转换为字典
        
        Returns:
            Dict[str, Any]: 任务状态字典
        """
        return {
            "task_id": self.task_id,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "stats": self.stats,
            "current_file": self.current_file,
            "last_update": self.last_update
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskState':
        """从字典创建任务状态
        
        Args:
            data: 任务状态字典
            
        Returns:
            TaskState: 任务状态对象
        """
        task = cls(data["task_id"], data["input_path"], data["output_path"])
        task.start_time = data["start_time"]
        task.end_time = data["end_time"]
        task.status = data["status"]
        task.stats = data["stats"]
        task.current_file = data["current_file"]
        task.last_update = data["last_update"]
        return task
    
    def update_progress(self, file_path: str, success: bool = True) -> None:
        """更新处理进度
        
        Args:
            file_path: 当前处理的文件路径
            success: 处理是否成功
        """
        self.current_file = file_path
        self.stats["processed"] += 1
        self.stats["processed_files"].append(file_path)
        
        if success:
            self.stats["success"] += 1
        else:
            self.stats["failed"] += 1
            self.stats["failed_files"].append(file_path)
        
        self.last_update = time.time()
    
    def skip_file(self, file_path: str) -> None:
        """标记文件为跳过
        
        Args:
            file_path: 跳过的文件路径
        """
        self.stats["skipped"] += 1
    
    def complete(self) -> None:
        """标记任务为完成"""
        self.status = "completed"
        self.end_time = time.time()
    
    def fail(self) -> None:
        """标记任务为失败"""
        self.status = "failed"
        self.end_time = time.time()
    
    def pause(self) -> None:
        """暂停任务"""
        self.status = "paused"
    
    def resume(self) -> None:
        """恢复任务"""
        self.status = "running"
    
    def get_elapsed_time(self) -> float:
        """获取任务已运行时间
        
        Returns:
            float: 已运行时间（秒）
        """
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比
        
        Returns:
            float: 进度百分比
        """
        if self.stats["total"] == 0:
            return 0.0
        return (self.stats["processed"] / self.stats["total"]) * 100


class TaskManager:
    """任务管理器，负责任务状态的保存、加载和显示"""
    
    def __init__(self, checkpoint_dir: Optional[str] = None):
        """初始化任务管理器
        
        Args:
            checkpoint_dir: 检查点目录，默认为项目根目录下的checkpoints目录
        """
        if checkpoint_dir:
            self.checkpoint_dir = checkpoint_dir
        else:
            # 获取项目根目录的checkpoints文件夹路径
            current_file = os.path.abspath(__file__)
            utils_dir = os.path.dirname(current_file)
            src_dir = os.path.dirname(utils_dir)
            project_root = os.path.dirname(src_dir)
            self.checkpoint_dir = os.path.join(project_root, 'checkpoints')
        
        # 确保检查点目录存在
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        self.current_task = None
        self.progress_display = None
    
    def create_task(self, input_path: str, output_path: str) -> TaskState:
        """创建新任务
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            
        Returns:
            TaskState: 任务状态对象
        """
        # 生成任务ID（使用时间戳和随机字符）
        import random
        import string
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        task_id = f"{timestamp}-{random_suffix}"
        
        # 创建任务状态
        self.current_task = TaskState(task_id, input_path, output_path)
        
        # 保存初始检查点
        self._save_checkpoint()
        
        return self.current_task
    
    def load_latest_task(self) -> Optional[TaskState]:
        """加载最新的未完成任务
        
        Returns:
            Optional[TaskState]: 任务状态对象，如果没有未完成任务则返回None
        """
        try:
            # 获取所有检查点文件
            checkpoint_files = [f for f in os.listdir(self.checkpoint_dir) 
                               if f.endswith('.json') and not f.endswith('_completed.json')]
            
            if not checkpoint_files:
                return None
            
            # 按修改时间排序，获取最新的检查点
            checkpoint_files.sort(key=lambda f: os.path.getmtime(
                os.path.join(self.checkpoint_dir, f)), reverse=True)
            
            latest_file = os.path.join(self.checkpoint_dir, checkpoint_files[0])
            
            # 加载检查点
            with open(latest_file, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
            
            # 创建任务状态
            self.current_task = TaskState.from_dict(task_data)
            
            # 检查任务状态
            if self.current_task.status == "completed" or self.current_task.status == "failed":
                # 如果任务已完成或失败，返回None
                self.current_task = None
                return None
            
            # 将暂停的任务标记为运行中
            if self.current_task.status == "paused":
                self.current_task.resume()
            
            return self.current_task
            
        except Exception as e:
            logger.error(f"加载检查点时出错: {e}")
            return None
    
    def _save_checkpoint(self) -> bool:
        """保存当前任务状态到检查点文件
        
        Returns:
            bool: 保存是否成功
        """
        if not self.current_task:
            return False
        
        try:
            # 构建检查点文件路径
            status_suffix = "_completed" if self.current_task.status == "completed" else ""
            checkpoint_file = os.path.join(
                self.checkpoint_dir, f"{self.current_task.task_id}{status_suffix}.json")
            
            # 保存任务状态
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_task.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"保存检查点时出错: {e}")
            return False
    
    def update_progress(self, file_path: str, success: bool = True) -> None:
        """更新处理进度
        
        Args:
            file_path: 当前处理的文件路径
            success: 处理是否成功
        """
        if not self.current_task:
            return
        
        # 更新任务状态
        self.current_task.update_progress(file_path, success)
        
        # 更新进度显示
        if self.progress_display:
            self.progress_display(self.current_task.stats["processed"], 
                                 self.current_task.stats["total"],
                                 file_path)
        
        # 定期保存检查点（每处理10个文件或每30秒）
        if (self.current_task.stats["processed"] % 10 == 0 or 
            time.time() - self.current_task.last_update > 30):
            self._save_checkpoint()
    
    def skip_file(self, file_path: str) -> None:
        """标记文件为跳过
        
        Args:
            file_path: 跳过的文件路径
        """
        if not self.current_task:
            return
        
        self.current_task.skip_file(file_path)
    
    def complete_task(self) -> Dict[str, Any]:
        """完成当前任务
        
        Returns:
            Dict[str, Any]: 任务统计信息
        """
        if not self.current_task:
            return {}
        
        # 标记任务为完成
        self.current_task.complete()
        
        # 保存最终检查点
        self._save_checkpoint()
        
        # 返回统计信息
        stats = self.current_task.stats.copy()
        stats["elapsed_time"] = self.current_task.get_elapsed_time()
        stats["output_path"] = self.current_task.output_path
        
        return stats
    
    def fail_task(self) -> Dict[str, Any]:
        """标记当前任务为失败
        
        Returns:
            Dict[str, Any]: 任务统计信息
        """
        if not self.current_task:
            return {}
        
        # 标记任务为失败
        self.current_task.fail()
        
        # 保存最终检查点
        self._save_checkpoint()
        
        # 返回统计信息
        stats = self.current_task.stats.copy()
        stats["elapsed_time"] = self.current_task.get_elapsed_time()
        stats["output_path"] = self.current_task.output_path
        
        return stats
    
    def pause_task(self) -> bool:
        """暂停当前任务
        
        Returns:
            bool: 暂停是否成功
        """
        if not self.current_task:
            return False
        
        # 标记任务为暂停
        self.current_task.pause()
        
        # 保存检查点
        return self._save_checkpoint()
    
    def resume_task(self) -> bool:
        """恢复当前任务
        
        Returns:
            bool: 恢复是否成功
        """
        if not self.current_task:
            return False
        
        # 标记任务为运行中
        self.current_task.resume()
        
        # 保存检查点
        return self._save_checkpoint()
    
    def get_unfinished_files(self) -> List[str]:
        """获取未处理的文件列表
        
        Returns:
            List[str]: 未处理的文件路径列表
        """
        if not self.current_task:
            return []
        
        # 获取已处理的文件集合
        processed_files = set(self.current_task.stats["processed_files"])
        
        # 如果是目录，获取所有文件
        if os.path.isdir(self.current_task.input_path):
            all_files = []
            for root, _, files in os.walk(self.current_task.input_path):
                for file in files:
                    all_files.append(os.path.join(root, file))
            
            # 返回未处理的文件
            return [f for f in all_files if f not in processed_files]
        
        # 如果是单个文件且未处理
        if self.current_task.input_path not in processed_files:
            return [self.current_task.input_path]
        
        return []
    
    def setup_progress_display(self) -> None:
        """设置进度显示"""
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        task = progress.add_task("处理文件", total=self.current_task.stats["total"])
        
        # 启动进度显示
        progress.start()
        
        def update_progress(completed: int, total: int, current_file: str):
            # 更新进度条
            progress.update(task, completed=completed, total=total, 
                           description=f"处理文件 ({completed}/{total})")
            
            # 显示当前处理的文件
            file_name = os.path.basename(current_file)
            progress.console.print(f"当前: {file_name}", end="\r")
        
        self.progress_display = update_progress
    
    def generate_report(self, stats: Dict[str, Any]) -> str:
        """生成任务报告
        
        Args:
            stats: 任务统计信息
            
        Returns:
            str: 报告文本
        """
        # 格式化时间
        elapsed_time = stats.get("elapsed_time", 0)
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours)}小时{int(minutes)}分{int(seconds)}秒" if hours > 0 else \
                  f"{int(minutes)}分{int(seconds)}秒" if minutes > 0 else \
                  f"{seconds:.2f}秒"
        
        # 构建报告文本
        report = [
            "任务执行报告",
            "===========",
            f"总文件数: {stats.get('total', 0)}",
            f"成功处理: {stats.get('success', 0)}",
            f"处理失败: {stats.get('failed', 0)}",
            f"跳过文件: {stats.get('skipped', 0)}",
            f"处理用时: {time_str}",
            f"输出目录: {stats.get('output_path', '')}"
        ]
        
        # 添加失败文件列表
        if stats.get('failed', 0) > 0 and 'failed_files' in stats:
            report.append("\n失败的文件:")
            for file in stats['failed_files']:
                report.append(f"  - {file}")
        
        return "\n".join(report)
    
    def save_report(self, stats: Dict[str, Any]) -> Optional[str]:
        """保存任务报告到文件
        
        Args:
            stats: 任务统计信息
            
        Returns:
            Optional[str]: 报告文件路径，保存失败则返回None
        """
        if not stats:
            return None
        
        try:
            # 生成报告文本
            report_text = self.generate_report(stats)
            
            # 构建报告文件路径
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            report_file = os.path.join(self.checkpoint_dir, f"report_{timestamp}.txt")
            
            # 保存报告
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            return report_file
            
        except Exception as e:
            logger.error(f"保存报告时出错: {e}")
            return None
    
    def display_report(self, stats: Dict[str, Any]) -> None:
        """在终端显示任务报告
        
        Args:
            stats: 任务统计信息
        """
        if not stats:
            return
        
        # 生成报告文本
        report_text = self.generate_report(stats)
        
        # 在终端显示报告
        console.print(Panel(report_text, title="任务执行报告", expand=False))