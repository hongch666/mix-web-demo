import traceback
from typing import Optional, Callable, Any
from sqlmodel import Session
from common.utils import fileLogger as logger, Constants


def update_analyze_caches(
    analyze_service: Optional[Any] = None,
    db_factory: Optional[Callable[[], Session]] = None,
) -> None:
    """
    更新分析接口的所有缓存
    
    调用的 service 函数包括:
    1. get_top10_articles_service - 前10篇文章
    2. get_wordcloud_service - 词云图
    3. get_article_statistics_service - 文章统计信息
    4. get_category_article_count_service - 按分类统计文章数量
    5. get_monthly_publish_count_service - 月度文章发布统计
    
    Args:
        analyze_service: AnalyzeService 实例
        db_factory: 获取数据库连接的工厂函数
    """
    if analyze_service is None:
        logger.warning(Constants.UPDATE_ANALYZE_CACHES_ANALYZE_SERVICE_NONE_MESSAGE)
        return
    
    db = None
    try:
        # 获取数据库连接
        if db_factory:
            db = db_factory()
        
        logger.info(Constants.UPDATE_ANALYZE_CACHES_START_MESSAGE)
        
        # 1. 更新前10篇文章缓存
        try:
            logger.info(Constants.UPDATE_ANALYZE_CACHES_TOP10_START_MESSAGE)
            analyze_service.get_top10_articles_service(db)
            logger.info(Constants.UPDATE_ANALYZE_CACHES_TOP10_SUCCESS_MESSAGE)
        except Exception as e:
            logger.error(f"前10篇文章缓存更新失败: {e}")
            logger.debug(traceback.format_exc())
        
        # 2. 更新词云图缓存
        try:
            logger.info(Constants.UPDATE_ANALYZE_CACHES_WORDCLOUD_START_MESSAGE)
            analyze_service.get_wordcloud_service()
            logger.info(Constants.UPDATE_ANALYZE_CACHES_WORDCLOUD_SUCCESS_MESSAGE)
        except Exception as e:
            logger.error(f"词云图缓存更新失败: {e}")
            logger.debug(traceback.format_exc())
        
        # 3. 更新文章统计信息缓存
        try:
            logger.info(Constants.UPDATE_ANALYZE_CACHES_STATISTICS_START_MESSAGE)
            analyze_service.get_article_statistics_service(db)
            logger.info(Constants.UPDATE_ANALYZE_CACHES_STATISTICS_SUCCESS_MESSAGE)
        except Exception as e:
            logger.error(f"文章统计信息缓存更新失败: {e}")
            logger.debug(traceback.format_exc())
        
        # 4. 更新按分类统计文章数量缓存
        try:
            logger.info(Constants.UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_START_MESSAGE)
            analyze_service.get_category_article_count_service(db)
            logger.info(Constants.UPDATE_ANALYZE_CACHES_CATEGORY_STATISTICS_SUCCESS_MESSAGE)
        except Exception as e:
            logger.error(f"按分类统计文章数量缓存更新失败: {e}")
            logger.debug(traceback.format_exc())
        
        # 5. 更新月度文章发布统计缓存
        try:
            logger.info(Constants.UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_START_MESSAGE)
            analyze_service.get_monthly_publish_count_service(db)
            logger.info(Constants.UPDATE_ANALYZE_CACHES_MONTHLY_STATISTICS_SUCCESS_MESSAGE)
        except Exception as e:
            logger.error(f"月度文章发布统计缓存更新失败: {e}")
            logger.debug(traceback.format_exc())
        
        logger.info(Constants.UPDATE_ANALYZE_CACHES_COMPLETE_MESSAGE)
        
    except Exception as e:
        logger.error(f"update_analyze_caches 发生异常: {e}")
        logger.debug(traceback.format_exc())
    finally:
        # 关闭数据库连接
        if db and hasattr(db, 'close'):
            try:
                db.close()
            except Exception as close_e:
                logger.debug(f"关闭数据库连接失败: {close_e}")
