"""
日志模块
提供统一的日志记录功能，支持文件输出和控制台输出
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.constants.config import settings


class LoggerManager:
    """日志管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if not LoggerManager._initialized:
            self.log_dir = self._ensure_log_dir()
            self.loggers = {}
            LoggerManager._initialized = True
    
    def _ensure_log_dir(self) -> Path:
        """确保日志目录存在"""
        # 从配置中获取日志文件路径，并提取目录
        error_log_path = getattr(settings, 'ERROR_LOG', 'logs/error.log')
        log_dir = Path(error_log_path).parent
        
        # 如果路径是相对路径，则相对于项目根目录
        if not log_dir.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / log_dir
        
        # 创建目录
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def _create_formatter(self, format_type: str = 'detailed') -> logging.Formatter:
        """创建日志格式化器"""
        if format_type == 'detailed':
            fmt = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        elif format_type == 'simple':
            fmt = '%(asctime)s - %(levelname)s - %(message)s'
        else:
            fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        return logging.Formatter(
            fmt=fmt,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _create_file_handler(
        self, 
        filename: str, 
        level: int = logging.ERROR,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 10,
        format_type: str = 'detailed'
    ) -> logging.handlers.RotatingFileHandler:
        """创建文件处理器"""
        log_file = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            mode='a',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(level)
        handler.setFormatter(self._create_formatter(format_type))
        return handler
    
    def _create_console_handler(
        self, 
        level: int = logging.INFO,
        format_type: str = 'simple'
    ) -> logging.StreamHandler:
        """创建控制台处理器"""
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(self._create_formatter(format_type))
        return handler
    
    def get_logger(
        self,
        name: str,
        log_file: Optional[str] = None,
        file_level: int = logging.ERROR,
        console_level: int = logging.INFO,
        enable_console: bool = True,
        enable_file: bool = True
    ) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            log_file: 日志文件名，默认为 error.log
            file_level: 文件日志级别
            console_level: 控制台日志级别
            enable_console: 是否启用控制台输出
            enable_file: 是否启用文件输出
            
        Returns:
            logging.Logger: 日志记录器
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # 设置为最低级别，由handler控制
        
        # 避免重复添加handler
        if logger.handlers:
            logger.handlers.clear()
        
        # 添加文件处理器
        if enable_file:
            if log_file is None:
                log_file = 'error.log'
            file_handler = self._create_file_handler(
                filename=log_file,
                level=file_level,
                format_type='detailed'
            )
            logger.addHandler(file_handler)
        
        # 添加控制台处理器
        if enable_console:
            console_handler = self._create_console_handler(
                level=console_level,
                format_type='simple'
            )
            logger.addHandler(console_handler)
        
        # 防止日志传播到父记录器
        logger.propagate = False
        
        self.loggers[name] = logger
        return logger


# 全局日志管理器实例
_logger_manager = LoggerManager()


def get_logger(
    name: str = 'app',
    log_file: Optional[str] = None,
    file_level: int = logging.ERROR,
    console_level: int = logging.INFO,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件名
        file_level: 文件日志级别
        console_level: 控制台日志级别
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        
    Returns:
        logging.Logger: 日志记录器
    """
    return _logger_manager.get_logger(
        name=name,
        log_file=log_file,
        file_level=file_level,
        console_level=console_level,
        enable_console=enable_console,
        enable_file=enable_file
    )


# 预定义的日志记录器
def get_error_logger() -> logging.Logger:
    """获取错误日志记录器"""
    return get_logger(
        name='error',
        log_file='error.log',
        file_level=logging.ERROR,
        console_level=logging.ERROR
    )


def get_access_logger() -> logging.Logger:
    """获取访问日志记录器"""
    return get_logger(
        name='access',
        log_file='access.log',
        file_level=logging.INFO,
        console_level=logging.WARNING
    )


def get_business_logger() -> logging.Logger:
    """获取业务日志记录器"""
    return get_logger(
        name='business',
        log_file='business.log',
        file_level=logging.INFO,
        console_level=logging.INFO
    )


def get_debug_logger() -> logging.Logger:
    """获取调试日志记录器"""
    return get_logger(
        name='debug',
        log_file='debug.log',
        file_level=logging.DEBUG,
        console_level=logging.DEBUG
    )


# 日志装饰器
def log_exception(logger: Optional[logging.Logger] = None):
    """
    异常日志装饰器
    
    用法:
        @log_exception()
        def some_function():
            pass
    """
    if logger is None:
        logger = get_error_logger()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_async_exception(logger: Optional[logging.Logger] = None):
    """
    异步函数异常日志装饰器
    
    用法:
        @log_async_exception()
        async def some_async_function():
            pass
    """
    if logger is None:
        logger = get_error_logger()
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise
        return wrapper
    return decorator
