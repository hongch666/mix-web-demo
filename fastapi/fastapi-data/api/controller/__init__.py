from .analyzeController import router as analyze_router
from .uploadController import router as upload_router

__all__ = [
    "analyze_router",
    "upload_router"
]