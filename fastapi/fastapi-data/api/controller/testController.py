from fastapi import APIRouter
from fastapi.responses import JSONResponse

from common.task import export_articles_to_csv_and_hive
from common.utils import success,fail,fileLogger
from common.decorators import log

router: APIRouter = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 调用定时任务（导出文章表到csv并同步hive）
@router.post("/task")
@log("手动触发文章表导出任务")
async def test_export_articles_task() -> JSONResponse:
    try:
        await export_articles_to_csv_and_hive()
        return success()
    except Exception as e:
        fileLogger.error(f"手动触发文章表导出任务失败: {e}")
        return fail(f"任务执行失败: {e}")