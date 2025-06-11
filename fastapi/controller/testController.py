from fastapi import APIRouter

from utils.response import success

router = APIRouter(
    prefix="/api_fastapi",
    tags=["测试接口"],
)

# 测试
@router.get("/fastapi")
def testfastapi():
    return success("Hello, I am FastAPI!")
