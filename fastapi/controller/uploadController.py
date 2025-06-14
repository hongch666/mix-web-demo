from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from dto.uploadDTO import UploadDTO
from po.listResponse import ListResponse
from po.article import Article
from config.mysql import SessionLocal,get_db
from service.analyzeService import upload_file
from utils.response import success

router = APIRouter(
    prefix="/upload",
    tags=["上传文件接口"],
)

@router.post("")
def get_wordcloud(data:UploadDTO):
    return success(upload_file(
        data.local_file, 
        data.oss_file
        ))