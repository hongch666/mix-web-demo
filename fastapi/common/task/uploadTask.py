from apscheduler.schedulers.background import BackgroundScheduler
from config.mysql import get_db
from sqlalchemy.orm import Session
from common.utils.writeLog import fileLogger as logger
from api.service.analyzeService import export_articles_to_excel, upload_excel_to_oss
from apscheduler.schedulers.base import BaseScheduler

def export_articles_job() -> None:
    db: Session = next(get_db())
    try:
        export_articles_to_excel(db)
        file_path: str = upload_excel_to_oss()
        logger.info(f"定时任务：文章表已自动备份到 {file_path}")
    except Exception as e:
        logger.error(f"定时任务备份文章表失败: {e}")

def start_scheduler() -> BaseScheduler:
    scheduler: BackgroundScheduler = BackgroundScheduler()
    # 每3小时执行一次导出文章表的任务
    scheduler.add_job(export_articles_job, 'interval', days=1)
    scheduler.start()
    logger.info("定时任务调度器已启动")
    return scheduler