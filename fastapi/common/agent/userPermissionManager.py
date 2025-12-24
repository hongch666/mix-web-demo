from typing import Optional
import re
from sqlmodel import Session
from common.utils import fileLogger as logger

class UserPermissionManager:
    """用户权限管理器"""
    
    ROLE_ADMIN = "admin"
    ROLE_USER = "user"
    
    # 个人信息查询的关键字
    PERSONAL_INFO_KEYWORDS = [
        "我的", "个人", "自己的", "本人的", "我", "自己",
        "点赞", "收藏", "喜欢", "评论", "互动", "关注"
    ]
    
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
    
    def is_personal_info_query(self, question: str) -> bool:
        """
        判断问题是否涉及个人信息查询
        
        Args:
            question: 用户问题
            
        Returns:
            True 如果是个人信息查询，否则 False
        """
        if not question:
            return False
        
        # 转换为小写便于匹配
        question_lower = question.lower()
        
        # 检查是否包含个人信息查询的关键字
        for keyword in self.PERSONAL_INFO_KEYWORDS:
            if keyword in question_lower:
                logger.debug(f"[权限] 检测到个人信息查询关键字: '{keyword}'")
                return True
        
        return False
    
    def can_access_sql_tools(self, user_id: int, db: Session, question: str = "") -> tuple[bool, str]:
        """
        检查用户是否有权使用 SQL 工具
        
        向后兼容的方法，调用新的 can_use_tool 方法
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            question: 用户问题
            
        Returns:
            (是否有权限, 原因说明)
        """
        return self.can_use_tool(user_id, db, 'sql', question)
    
    def can_access_mongodb_logs(self, user_id: int, db: Session, question: str = "") -> tuple[bool, str]:
        """
        检查用户是否有权查询 MongoDB 日志
        
        向后兼容的方法，调用新的 can_use_tool 方法
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            question: 用户问题
            
        Returns:
            (是否有权限, 原因说明)
        """
        return self.can_use_tool(user_id, db, 'mongodb', question)
    
    def can_use_tool(self, user_id: int, db: Session, tool_type: str, question: str = "") -> tuple[bool, str]:
        """
        检查用户是否有权使用指定的工具
        
        权限判断流程：
        1. 如果未登录，拒绝访问
        2. 如果是查询个人信息（包含关键字），所有登录用户都允许
        3. 如果不是个人信息查询，则检查用户角色是否为管理员
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            tool_type: 工具类型 ('sql' 或 'mongodb')
            question: 用户问题
            
        Returns:
            (是否有权限, 原因说明)
        """
        # 第一步：检查是否登录
        if not user_id:
            tool_name = "数据库查询" if tool_type == 'sql' else "日志查询"
            return False, f"权限拒绝：请先登录才能访问{tool_name}功能。您当前可以使用文章搜索和闲聊功能。"
        
        # 第二步：检查是否是个人信息查询
        if question and self.is_personal_info_query(question):
            logger.info(f"用户 {user_id} 查询个人信息，允许访问 {tool_type} 工具")
            return True, ""
        
        # 第三步：不是个人信息查询，检查用户角色（最后进行）
        role = self.get_user_role(user_id, db)
        if role == self.ROLE_ADMIN:
            logger.info(f"用户 {user_id} (角色: {role}) 有权访问 {tool_type} 工具")
            return True, ""
        else:
            tool_name = "数据库查询" if tool_type == 'sql' else "日志查询"
            reason = f"权限拒绝：您的账户权限不足，无法访问{tool_name}功能。仅管理员账户可以使用此功能。如需查询个人信息（如'我的点赞文章'），请在问题中包含相关关键词。"
            logger.warning(f"用户 {user_id} (角色: {role}) 尝试访问 {tool_type} 工具被拒绝：{question}")
            return False, reason
    
    def validate_database_query_permission(self, user_id: int, db: Session, question: str = "") -> tuple[bool, str]:
        """
        验证用户是否有权执行数据库查询
        
        向后兼容的方法，调用新的 can_use_tool 方法
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            question: 用户问题（用于更好的错误提示）
            
        Returns:
            (是否有权限, 原因说明)
        """
        return self.can_use_tool(user_id, db, 'sql', question)


def get_user_permission_manager(user_mapper=None) -> UserPermissionManager:
    """获取用户权限管理器单例"""
    return UserPermissionManager(user_mapper)
