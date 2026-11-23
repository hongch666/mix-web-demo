from pydantic import BaseModel, Field


class ApiLogResponse(BaseModel):
    """接口日志统计响应模型，包含平均响应时间与调用次数"""

    api_path: str = Field(description="API 路径")
    api_method: str = Field(description="请求方法")
    api_description: str = Field(description="API 描述")
    avg_response_time: float = Field(description="平均响应时间")
    call_count: int = Field(description="调用次数")
