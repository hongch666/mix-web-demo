from functools import lru_cache
from sqlmodel import Session, select
from entity.po import Comments
from entity.po.user import User

class CommentsMapper:
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

@lru_cache()
def get_comments_mapper() -> CommentsMapper:
    return CommentsMapper()