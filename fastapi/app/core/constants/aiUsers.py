class AiUsers:
    """AI 评论用户常量

    AI 评论的作者身份固定为以下用户，创建与初始化由 Spring 侧负责
    （Defaults、DatabaseInitializer 与 db/mysql/spring/user.sql），
    本服务只按 ID 写入评论，两侧取值需保持同步
    """

    # ===== AI 评论用户 =====

    CLAUDE_ID: int = 1001
    """Claude 评论作者的固定用户 ID，与 Spring 侧 Defaults 保持一致"""
    GEMINI_ID: int = 1002
    """Gemini 评论作者的固定用户 ID"""
    GPT_ID: int = 1003
    """GPT 评论作者的固定用户 ID"""
    DEEPSEEK_ID: int = 1004
    """DeepSeek 评论作者的固定用户 ID"""
    GLM_ID: int = 1005
    """GLM 评论作者的固定用户 ID"""
    QWEN_ID: int = 1006
    """Qwen 评论作者的固定用户 ID"""
