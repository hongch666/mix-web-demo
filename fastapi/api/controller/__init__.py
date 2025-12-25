from .analyzeController import router as analyze_router
from .apilogController import router as apilog_router
from .chatController import router as chat_router
from .generateController import router as generate_router
from .testController import router as test_router
from .uploadController import router as upload_router
from .aiHistoryController import router as ai_history_router

__all__ = [
    "analyze_router",
    "apilog_router",
    "chat_router",
    "generate_router",
    "test_router",
    "upload_router",
    "ai_history_router",
]