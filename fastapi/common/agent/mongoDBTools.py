from functools import lru_cache
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from langchain_core.tools import Tool
from common.config import load_config, db
from common.utils import fileLogger as logger, Constants

class MongoDBTools:
    """MongoDB 日志查询工具集"""
    
    def __init__(self) -> None:
        """初始化 MongoDB 日志工具"""
        self.db = db
        self.logger = logger
        # 获取日志集合名称（默认为 api_logs）
        self.logs_collection_name: str = load_config("database").get("mongodb", {}).get("logs_collection")
    
    def get_logs_collection(self) -> Optional[Any]:
        """获取日志集合"""
        try:
            return self.db[self.logs_collection_name]
        except Exception as e:
            self.logger.error(f"获取日志集合失败: {e}")
            return None

    def list_mongodb_collections(self, _: str = "") -> str:
        """列出 MongoDB 数据库中的所有 collection 及其基本信息"""
        try:
            collections_info: List[Dict[str, Any]] = []
            for collection_name in self.db.list_collection_names():
                try:
                    collection = self.db[collection_name]
                    doc_count = collection.count_documents({})

                    # 获取一个样本文档以了解结构
                    sample_doc = collection.find_one()
                    sample_keys = list(sample_doc.keys()) if sample_doc else []

                    collections_info.append({
                        "name": collection_name,
                        "document_count": doc_count,
                        "sample_fields": sample_keys[:10]  # 只显示前10个字段
                    })
                except Exception as e:
                    self.logger.warning(f"无法获取 {collection_name} 的信息: {e}")
                    collections_info.append({
                        "name": collection_name,
                        "error": str(e)
                    })

            return json.dumps(collections_info, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = f"获取 collection 列表失败: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    def query_mongodb(self, query_params: Union[str, Dict[str, Any]]) -> str:
        """通用的 MongoDB 查询工具，可以查询任意 collection"""
        try:
            # 解析 query_params
            try:
                if isinstance(query_params, str):
                    params = json.loads(query_params)
                else:
                    params = query_params
            except json.JSONDecodeError:
                return f"错误: query_params 必须是有效的 JSON 格式，收到: {query_params}"

            # 提取参数
            collection_name = params.get("collection_name", "")
            filter_dict = params.get("filter_dict", {})
            limit = params.get("limit", 10)

            # 验证必需参数
            if not collection_name:
                return Constants.COLLECTION_NAME_VALIDATION_ERROR

            # 确保 limit 是整数
            limit_int = int(limit) if isinstance(limit, str) else limit

            # 确保 filter_dict 是字典
            if isinstance(filter_dict, str):
                try:
                    filter_obj = json.loads(filter_dict)
                except json.JSONDecodeError:
                    return f"错误: filter_dict 必须是有效的 JSON 格式，收到: {filter_dict}"
            else:
                filter_obj = filter_dict if filter_dict else {}

            # 获取 collection
            collection = self.db[collection_name]

            # 执行查询
            cursor = collection.find(filter_obj).limit(limit_int)
            results: List[Dict[str, Any]] = []
            for doc in cursor:
                # 转换所有 datetime 对象为 ISO 格式字符串
                doc = self._convert_datetime_to_string(doc)
                results.append(doc)

            self.logger.info(f"查询 {collection_name}: 条件={filter_obj}, 返回 {len(results)} 条记录")
            return json.dumps(results, ensure_ascii=False, indent=2)

        except Exception as e:
            error_msg = f"MongoDB 查询失败: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    def get_langchain_tools(self) -> List[Tool]:
        """获取 LangChain Tool 对象列表"""
        return [
            Tool(
                name=Constants.MONGODB_LIST_COLLECTIONS_TOOL_NAME,
                description=Constants.MONGODB_LIST_COLLECTIONS_TOOL_DESC,
                func=self.list_mongodb_collections
            ),
            Tool(
                name=Constants.MONGODB_QUERY_TOOL_NAME,
                description=Constants.MONGODB_QUERY_TOOL_DESC,
                func=self.query_mongodb
            )
        ]
    
    def _convert_datetime_to_string(self, obj: Any) -> Any:
        """递归转换所有 datetime 对象为 ISO 格式字符串"""
        
        if isinstance(obj, dict):
            # 处理字典中的所有值
            result: Dict[str, Any] = {}
            for key, value in obj.items():
                if isinstance(value, ObjectId):
                    result[key] = str(value)
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, dict):
                    result[key] = self._convert_datetime_to_string(value)
                elif isinstance(value, list):
                    result[key] = self._convert_datetime_to_string(value)
                else:
                    result[key] = value
            return result
        elif isinstance(obj, list):
            # 处理列表中的所有元素
            return [self._convert_datetime_to_string(item) for item in obj]
        elif isinstance(obj, datetime):
            # 直接转换 datetime
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            # 转换 ObjectId
            return str(obj)
        else:
            # 返回原值
            return obj
    
    def _format_results(self, results: Any) -> str:
        """将结果格式化为字符串"""
        try:
            return json.dumps(results, ensure_ascii=False, indent=2)
        except:
            return str(results)

@lru_cache
def get_mongodb_tools() -> MongoDBTools:
    """获取 MongoDB 日志工具实例"""
    return MongoDBTools()
