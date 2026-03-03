from .user.userRouter import router as userRouter
from .chat.chatRouter import router as chatRouter
from .analyze.analyzeRouter import router as analyzeRouter
from .generate.generateRouter import router as generateRouter
from .upload.uploadRouter import router as uploadRouter
from .aiHistory.aiHistoryRouter import router as aiHistoryRouter
from .apiLog.apiLogRouter import router as apiLogRouter
from .test.testRouter import router as testRouter

__all__ = [
    "userRouter",
    "chatRouter",
    "analyzeRouter",
    "generateRouter",
    "uploadRouter",
    "aiHistoryRouter",
    "apiLogRouter",
    "testRouter",
]
