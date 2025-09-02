from .chatController import router as chat_router
from .generateController import router as generate_router

__all__ = [
    "chat_router",
    "generate_router"
]