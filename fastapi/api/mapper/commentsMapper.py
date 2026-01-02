from functools import lru_cache
from sqlmodel import Session, select
from entity.po import Comments
from entity.po.user import User
from datetime import datetime
from sqlalchemy import func as sa_func, cast, Date
from common.utils import fileLogger as logger

class CommentsMapper:
    """评论 Mapper"""
    
    def get_ai_comments_num_by_article_id_mapper(self, article_id: int, db: Session) -> int:
        # 第一步: 查询所有 role 为 "ai" 的用户ID
        ai_user_statement = select(User.id).where(User.role == "ai")
        ai_user_ids = db.exec(ai_user_statement).all()
        
        # 如果没有AI用户,直接返回0
        if not ai_user_ids:
            return 0
        
        # 第二步: 查询当前文章中,用户ID在AI用户ID数组范围内的评论总数
        comments_statement = select(Comments).where(
            Comments.article_id == article_id,
            Comments.user_id.in_(ai_user_ids)
        )
        ai_comments = db.exec(comments_statement).all()
        
        return len(ai_comments)
    
    def create_comment_mapper(self, comment: Comments, db: Session) -> Comments:
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    def delete_ai_comments_by_article_id_mapper(self, article_id: int, db: Session) -> None:
        # 查询所有 role 为 "ai" 的用户ID
        ai_user_statement = select(User.id).where(User.role == "ai")
        ai_user_ids = db.exec(ai_user_statement).all()
        comments_statement = select(Comments).where(
            Comments.article_id == article_id,
            Comments.user_id.in_(ai_user_ids)
        )
        comments_to_delete = db.exec(comments_statement).all()
        
        for comment in comments_to_delete:
            db.delete(comment)
        
        db.commit()

    def get_monthly_comment_trend_mapper(self, db: Session, user_id: int) -> dict:
        """获取用户本月评论的趋势"""
        try:
            today = datetime.now()
            first_day = datetime(today.year, today.month, 1)
            if today.month == 12:
                last_day = datetime(today.year + 1, 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                last_day = datetime(today.year, today.month + 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
            
            statement = select(
                cast(Comments.create_time, Date).label("date"),
                sa_func.count(Comments.id).label("count")
            ).where(
                Comments.user_id == user_id,
                Comments.create_time >= first_day,
                Comments.create_time < last_day
            ).group_by(cast(Comments.create_time, Date)).order_by(cast(Comments.create_time, Date))
            
            results = db.exec(statement).all()
            
            daily_trends = []
            total = 0
            for row in results:
                date_str = str(row[0])
                count = row[1]
                daily_trends.append({
                    "date": date_str,
                    "count": count
                })
                total += count
            
            logger.debug(f"用户 {user_id} 本月评论趋势: 总数={total}, 天数={len(daily_trends)}")
            return {
                "total": total,
                "daily_trends": daily_trends
            }
        except Exception as e:
            logger.error(f"获取评论趋势失败: {e}", exc_info=True)
            return {"total": 0, "daily_trends": []}

@lru_cache()
def get_comments_mapper() -> CommentsMapper:
    return CommentsMapper()