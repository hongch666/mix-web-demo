from apscheduler.schedulers.background import BackgroundScheduler
from config.mysql import get_db
from sqlalchemy.orm import Session
from common.utils.writeLog import fileLogger as logger
from api.service.analyzeService import export_articles_to_excel,upload_excel_to_oss

def export_articles_job():
    db: Session = next(get_db())
    try:
        export_articles_to_excel(db)
        file_path:str = upload_excel_to_oss()
        logger.info(f"定时任务：文章表已自动导出到 {file_path}")
    except Exception as e:
        logger.error(f"定时任务导出文章表失败: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # 每小时执行一次导出文章表的任务
    scheduler.add_job(export_articles_job, 'interval', hours=1)
    scheduler.start()
    logger.info("定时任务调度器已启动")