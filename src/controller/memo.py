from fastapi import APIRouter, Body, Depends, Path, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.config import limiter
from src.constants.constant import Error, ErrorMes
from src.model import req, resp
from src.service import memo_util
from src.storage.db import get_db

# 添加日志导入
from src.utils.logger import get_error_logger, get_business_logger

memoRouter = APIRouter(prefix="/api/memo", tags=["memo"])

# 创建日志记录器
error_logger = get_error_logger()
business_logger = get_business_logger()

@memoRouter.get("/ping")
def pong():
    """healthcheck"""
    return Response(content="pong")


@memoRouter.get("/", response_model=resp.MemoResponse)
@limiter.limit("5/seconds")
async def Get_all(request: Request, response: Response, session: AsyncSession = Depends(get_db)):
    """获取备忘录"""
    try:
        business_logger.info("开始获取所有备忘录")
        memos_row = await memo_util.find_memo_all(session)
        business_logger.info(f"成功获取 {len(memos_row)} 条备忘录")
    except Exception as e:
        error_logger.error(f"获取备忘录失败: {str(e)}", exc_info=True)
        raise resp.ErrResponse(Error.DbErr, "fail to get memo:Unkown Error Happened", status.HTTP_500_INTERNAL_SERVER_ERROR)


    memo_list = []
    for memo_row in memos_row:
        memo = resp.MemoSchema.model_validate(memo_row._asdict())
        memo_list.append(memo)

    return resp.MemoResponse(memos=memo_list)


@memoRouter.post("/")
@limiter.limit("1/seconds")
async def Create_memo(request: Request, response: Response, create_body: req.CreateMemoRequest = Body(), sess: AsyncSession = Depends(get_db)):
    """创建备忘录"""

    try:
        business_logger.info(f"开始创建备忘录: {create_body.title}")
        memo = await memo_util.create_memo(create_body, sess)
        business_logger.info(f"成功创建备忘录: id={memo.id}")
    except Exception as e:
        error_logger.error(f"创建备忘录失败: {str(e)}", exc_info=True)
        raise resp.ErrResponse(Error.DbErr, "fail to create memo:Unkown Error Happened", status.HTTP_500_INTERNAL_SERVER_ERROR)
    return resp.APIResponse(errCode=Error.NoError)


@memoRouter.patch("/{id}")
@limiter.limit("1/seconds")
async def Update_memo(request: Request, response: Response, id: int = Path(), update_body: req.UpdateMemoRequest = Body(), sess: AsyncSession = Depends(get_db)):
    """更新备忘录"""

    # try:
    #     raw_body = await request.json()
    #     print("--- 诊断信息：收到 PATCH 请求的原始数据 ---")
    #     print(raw_body)
    #     print(f"数据类型: {type(raw_body)}")
    #     print("---------------------------------------------")
    # except Exception as e:
    #     print("--- 诊断信息：读取原始请求数据时出错 ---")
    #     print(e)
    #     print("-------------------------------------------")
        
    try:
        memo_row = await memo_util.find_memo_by_id(id, sess)
    except Exception:
        raise resp.ErrResponse(Error.DbErr, "fail to get memo:Unkown Error Happened", status.HTTP_500_INTERNAL_SERVER_ERROR)

    if memo_row is None:
        raise resp.ErrResponse(Error.MemoNotFound, ErrorMes[Error.MemoNotFound], status.HTTP_404_NOT_FOUND)

    try:
        memo_new = await memo_util.update_memo(memo_row.id, update_body.model_dump(exclude_none=True), sess)
    except Exception:
        raise resp.ErrResponse(Error.DbErr, "fail to update memo:Unkown Error Happened", status.HTTP_500_INTERNAL_SERVER_ERROR)

    return resp.APIResponse(errCode=Error.NoError)


@memoRouter.delete("/{id}")
@limiter.limit("1/seconds")
async def Delete_memo(request: Request, response: Response, id: int = Path(), sess: AsyncSession = Depends(get_db)):
    """删除备忘录"""
    try:
        memo_row = await memo_util.find_memo_by_id(id, sess)
    except Exception:
        raise resp.ErrResponse(Error.DbErr, "fail to get memo:Unkown Error Happened", status.HTTP_500_INTERNAL_SERVER_ERROR)
    if memo_row is None:
        raise resp.ErrResponse(Error.NoMsg, ErrorMes[Error.NoMsg], status.HTTP_404_NOT_FOUND)

    try:
        await memo_util.delete_memo(id, sess)
    except Exception:
        raise resp.ErrResponse(Error.DbErr, "fail to delete product:Unkown Error Happened", status.HTTP_500_INTERNAL_SERVER_ERROR)

    return resp.APIResponse(errCode=Error.NoError)
