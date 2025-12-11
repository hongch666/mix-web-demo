from typing import Optional
from sqlmodel import Session, select
from common.utils import fileLogger as logger


class UserPermissionManager:
    """用户权限管理器"""
    
    ROLE_ADMIN = "admin"
    ROLE_USER = "user"
    
    def __init__(self, user_mapper=None):
        """
        初始化权限管理器
        
        Args:
            user_mapper: 用户 Mapper 实例
        """
        self.user_mapper = user_mapper
    
    def get_user_role(self, user_id: int, db: Session) -> Optional[str]:
        """
        获取用户角色
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            用户角色：'admin' 或 'user'，如果用户不存在返回 'user'
        """
        try:
            if not self.user_mapper:
                logger.warning(f"用户Mapper未初始化，无法获取用户 {user_id} 的角色，使用默认角色 'user'")
                return self.ROLE_USER  # 默认为 user
            
            # 直接调用 user_mapper 的 get_user_role 方法
            role = self.user_mapper.get_user_role(user_id, db)
            logger.info(f"用户 {user_id} 的角色: {role}")
            return role
            
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的角色失败: {e}，使用默认角色 'user'")
            return self.ROLE_USER  # 异常时默认为 user
    
    def is_admin(self, user_id: int, db: Session) -> bool:
        """
        检查用户是否为管理员
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            True 如果用户是管理员，否则 False
        """
        role = self.get_user_role(user_id, db)
        return role == self.ROLE_ADMIN
    
    def can_access_sql_tools(self, user_id: int, db: Session) -> tuple[bool, str]:
        """
        检查用户是否有权使用 SQL 工具
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            (是否有权限, 原因说明)
        """
        if not user_id:
            return False, "请先登录"
        
        role = self.get_user_role(user_id, db)
        if role == self.ROLE_ADMIN:
            return True, "管理员用户有权访问SQL工具"
        else:
            return False, "普通用户无权访问SQL工具，只能使用文章搜索功能"
    
    def can_access_mongodb_logs(self, user_id: int, db: Session) -> tuple[bool, str]:
        """
        检查用户是否有权查询 MongoDB 日志
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            (是否有权限, 原因说明)
        """
        if not user_id:
            return False, "请先登录"
        
        role = self.get_user_role(user_id, db)
        if role == self.ROLE_ADMIN:
            return True, "管理员用户有权查询日志"
        else:
            return False, "普通用户无权查询日志，只能使用文章搜索功能"
    
    def validate_database_query_permission(self, user_id: int, db: Session, question: str = "") -> tuple[bool, str]:
        """
        验证用户是否有权执行数据库查询
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            question: 用户问题（用于更好的错误提示）
            
        Returns:
            (是否有权限, 原因说明)
        """
        if not user_id:
            return False, "请先登录后进行数据查询"
        
        role = self.get_user_role(user_id, db)
        
        if role == self.ROLE_ADMIN:
            return True, ""
        else:
            msg = f"您没有权限查询数据库。{question if question else ''}"
            logger.warning(f"用户 {user_id} (角色: {role}) 尝试执行数据库查询但被拒绝: {msg}")
            return False, msg


def get_user_permission_manager(user_mapper=None) -> UserPermissionManager:
    """获取用户权限管理器单例"""
    return UserPermissionManager(user_mapper)
