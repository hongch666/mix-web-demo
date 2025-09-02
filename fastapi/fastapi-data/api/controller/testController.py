from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any, Dict

from common.client import call_remote_service
from common.task import export_articles_to_csv_and_hive
from common.utils import success,fail,fileLogger
from common.middleware import get_current_user_id, get_current_username

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 调用定时任务（导出文章表到csv并同步hive）
@router.post("/task")
async def test_export_articles_task() -> JSONResponse:
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    fileLogger.info(f"用户{user_id}:{username} GET /api_fastapi/task: 手动触发文章表导出任务")
    try:
        await export_articles_to_csv_and_hive()
        return success()
    except Exception as e:
        fileLogger.error(f"手动触发文章表导出任务失败: {e}")
        return fail(f"任务执行失败: {e}")