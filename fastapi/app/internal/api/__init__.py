from typing import List

from fastapi import APIRouter

from .aiHistory.aiHistoryRouter import router as aiHistoryRouter
from .analyze.analyzeRouter import router as analyzeRouter
from .apiLog.apiLogRouter import router as apiLogRouter
from .chat.chatRouter import router as chatRouter
from .generate.generateRouter import router as generateRouter
from .graphSearch.graphSearchRouter import router as graphSearchRouter
from .test.testRouter import router as testRouter
from .user.userRouter import router as userRouter
from .vectorSearch.vectorSearchRouter import router as vectorSearchRouter

# 所有路由列表
routers: List[APIRouter] = [
    analyzeRouter,
    apiLogRouter,
    chatRouter,
    generateRouter,
    testRouter,
    aiHistoryRouter,
    userRouter,
    graphSearchRouter,
    vectorSearchRouter,
]

__all__: List[str] = [
    "routers",
    "userRouter",
    "chatRouter",
    "analyzeRouter",
    "generateRouter",
    "aiHistoryRouter",
    "apiLogRouter",
    "testRouter",
    "graphSearchRouter",
    "vectorSearchRouter",
]
