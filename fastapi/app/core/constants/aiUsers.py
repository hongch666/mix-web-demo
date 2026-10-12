class AiUsers:
    """AI 评论用户常量

    AI 评论的作者身份固定为以下用户，创建与初始化由 Spring 侧负责
    （Defaults、DatabaseInitializer 与 db/mysql/spring/user.sql），
    本服务只按 ID 写入评论，两侧取值需保持同步
    """

    CLAUDE_ID: int = 1001
    GEMINI_ID: int = 1002
    GPT_ID: int = 1003
    DEEPSEEK_ID: int = 1004
    GLM_ID: int = 1005
    QWEN_ID: int = 1006
