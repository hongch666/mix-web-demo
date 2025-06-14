from pydantic import BaseModel

class UploadDTO(BaseModel):
    local_file: str
    oss_file: str