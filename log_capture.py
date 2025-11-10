"""
日志捕获工具 - 用于将print输出重定向到进度回调
"""
import sys
from typing import Callable, Optional
from io import StringIO


class LogCapture:
    """捕获print输出并转发到回调函数"""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        self.callback = callback
        self.original_stdout = sys.stdout
        self.buffer = []
        self.current_line = ''
    
    def write(self, text: str):
        """重写write方法，捕获输出"""
        # 处理换行符
        if '\n' in text:
            parts = text.split('\n')
            # 第一部分追加到当前行
            self.current_line += parts[0]
            if self.current_line.strip():
                self._process_line(self.current_line.strip())
            # 处理中间的部分（完整的行）
            for part in parts[1:-1]:
                if part.strip():
                    self._process_line(part.strip())
            # 最后一部分作为新的当前行
            self.current_line = parts[-1]
        else:
            self.current_line += text
    
    def _process_line(self, line: str):
        """处理一行日志"""
        # 过滤掉tqdm的进度条（包含特殊字符）
        if '\r' in line or '\x1b' in line:
            # 提取实际内容（去除ANSI转义码）
            import re
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)  # 移除ANSI颜色码
            line = line.replace('\r', '').strip()
            if not line:
                return
        
        if line and self.callback:
            self.callback(line)
        elif line:
            self.buffer.append(line)
    
    def flush(self):
        """刷新缓冲区"""
        if self.current_line.strip():
            self._process_line(self.current_line.strip())
            self.current_line = ''
    
    def __enter__(self):
        """进入上下文管理器"""
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        self.flush()  # 确保最后一行也被处理
        sys.stdout = self.original_stdout
        return False

