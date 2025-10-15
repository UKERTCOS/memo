"""启动函数"""

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """startup event"""
    # 初始化日志
    # 初始化数据库
    init_logger()
    await init_database()

    yield


app = FastAPI(lifespan=lifespan)
@app.get("/")
def read_root():
    return {"message": "Welcome to Docker2"}

# 路由
app.include_router(memo.memoRouter)

# 自定义异常处理
@app.exception_handler(ErrResponse)
async def err_response_exception_handler(request: Request, exc: ErrResponse):
    if exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        excMes = traceback.format_exc()
        endIndex = excMes.rfind("During handling of the above exception, another exception occurred:")
        errMes = excMes[:endIndex]
        errorlogger.error(errMes)
        print(errMes)
    if exc.status_code != status.HTTP_200_OK:
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



accesslogger = logging.getLogger("uvicorn.access")
errorlogger = logging.getLogger("memo.error")


def init_logger():
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False

    # Ensure we write structured error details to a rotating file so production errors persist.
    error_logger = logging.getLogger("memo.error")
    error_logger.setLevel(logging.INFO)
    error_logger.propagate = False

    def _ensure_directory(path: str) -> None:
        directory = os.path.dirname(os.path.abspath(path))
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _attach_rotating_handler(logger: logging.Logger, file_path: str, formatter: logging.Formatter) -> None:
        _ensure_directory(file_path)
        normalized_path = os.path.abspath(file_path)
        existing = [
            h
            for h in logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
            and os.path.abspath(getattr(h, "baseFilename", "")) == normalized_path
        ]
        if existing:
            return
        handler = logging.handlers.RotatingFileHandler(
            normalized_path,
            mode="a",
            maxBytes=1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        handler.setLevel(logger.level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    access_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    error_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    _attach_rotating_handler(access_logger, settings.ACCESS_LOG, access_formatter)
    _attach_rotating_handler(error_logger, settings.ERROR_LOG, error_formatter)

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(logging.INFO)
    uvicorn_error_logger.propagate = False
    _attach_rotating_handler(uvicorn_error_logger, settings.ERROR_LOG, error_formatter)


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
