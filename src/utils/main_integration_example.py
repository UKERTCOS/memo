"""
如何在现有项目中集成日志模块的示例

这个文件展示了如何将新的日志模块集成到 main.py 中
"""

# 原有的导入
import logging
import logging.handlers
import os
import sys
import traceback
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

pythonpath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, pythonpath)

from src.constants.config import corsConfig, limiter, settings
from src.controller import memo
from src.model.resp import ErrResponse
from src.storage.db import Base, engine

# === 新增：导入日志模块 ===
from src.utils.logger import get_error_logger, get_access_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """startup event"""
    # 初始化数据库
    await init_database()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Welcome to Docker2"}


# 路由
app.include_router(memo.memoRouter)


# === 修改：使用新的日志记录器 ===
# 获取日志记录器实例
errorlogger = get_error_logger()
accesslogger = get_access_logger()


# 自定义异常处理
@app.exception_handler(ErrResponse)
async def err_response_exception_handler(request: Request, exc: ErrResponse):
    if exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        excMes = traceback.format_exc()
        endIndex = excMes.rfind("During handling of the above exception, another exception occurred:")
        errMes = excMes[:endIndex] if endIndex != -1 else excMes
        # 使用新的日志记录器
        errorlogger.error(errMes)
        print(errMes)
    if exc.status_code != status.HTTP_200_OK:
        # 使用新的日志记录器
        errorlogger.info(exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"code": exc.errCode, "message": exc.message}),
    )


# 限流
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# 数据库初始化
async def init_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# === 删除或简化：原有的 init_logger 函数已不再需要 ===
# 因为新的日志模块会自动管理日志配置
# 如果需要兼容旧代码，可以保留一个空函数
def init_logger():
    """保留此函数以兼容旧代码，但实际工作由日志模块完成"""
    pass


# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 测试接口
@app.get("/ping")
def pong():
    """healthcheck"""
    return Response(content="pong")


# === 可选：添加请求日志中间件 ===
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求"""
    import time
    
    # 记录请求开始
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 记录请求结束
    process_time = (time.time() - start_time) * 1000
    accesslogger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time:.2f}ms"
    )
    
    return response
