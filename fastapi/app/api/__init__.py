from typing import List

from fastapi import APIRouter

from .aiHistory.aiHistoryRouter import router as aiHistoryRouter
from .analyze.analyzeRouter import router as analyzeRouter
from .apiLog.apiLogRouter import router as apiLogRouter
from .chat.chatRouter import router as chatRouter
from .generate.generateRouter import router as generateRouter
from .test.testRouter import router as testRouter
from .upload.uploadRouter import router as uploadRouter
from .user.userRouter import router as userRouter

# 所有路由列表
routers: List[APIRouter] = [
    analyzeRouter,
    apiLogRouter,
    chatRouter,
    generateRouter,
    testRouter,
    uploadRouter,
    aiHistoryRouter,
    userRouter,
]

__all__: List[str] = [
    "routers",
    "userRouter",
    "chatRouter",
    "analyzeRouter",
    "generateRouter",
    "uploadRouter",
    "aiHistoryRouter",
    "apiLogRouter",
    "testRouter",
]
