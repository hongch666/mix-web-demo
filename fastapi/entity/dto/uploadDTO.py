from pydantic import BaseModel, Field

class UploadDTO(BaseModel):
    local_file: str = Field(
        ...,
        min_length=5,
        description="本地文件路径，必须以/开头，且不能包含空格"
    )
    oss_file: str = Field(
        ...,
        min_length=5,
        description="OSS文件路径，必须以 bucket- 开头"
    )