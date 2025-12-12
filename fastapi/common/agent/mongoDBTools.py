import json
from datetime import datetime
from bson import ObjectId
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from langchain_core.tools import tool
from pymongo import DESCENDING
from config import load_config
from config.mongodb import db
from common.utils import fileLogger as logger

class MongoDBTools:
    """MongoDB 日志查询工具集"""
    
    def __init__(self):
        """初始化 MongoDB 日志工具"""
        self.db = db
        self.logger = logger
        # 获取日志集合名称（默认为 api_logs）
        self.logs_collection_name = load_config("database").get("mongodb", {}).get("logs_collection", "api_logs")
    
    def get_logs_collection(self):
        """获取日志集合"""
        try:
            return self.db[self.logs_collection_name]
        except Exception as e:
            self.logger.error(f"获取日志集合失败: {e}")
            return None
    
    def query_api_logs(
        self,
        user_id: Optional[int] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查询 API 日志
        
        Args:
            user_id: 用户 ID
            path: 请求路径
            method: HTTP 方法 (GET, POST, etc.)
            start_time: 开始时间 (ISO 格式或相对时间如 "1h", "1d")
            end_time: 结束时间 (ISO 格式或相对时间)
            limit: 返回结果数量限制
            
        Returns:
            日志列表
        """
        try:
            collection = self.get_logs_collection()
            if collection is None:
                return []
            
            # 构建查询过滤器
            filter_dict = {}
            
            if user_id:
                filter_dict["user_id"] = user_id
            
            if path:
                # 支持模糊匹配
                filter_dict["path"] = {"$regex": path, "$options": "i"}
            
            if method:
                filter_dict["method"] = method.upper()
            
            # 处理时间过滤
            time_filter = {}
            if start_time:
                start_dt = self._parse_datetime(start_time)
                if start_dt:
                    time_filter["$gte"] = start_dt
            
            if end_time:
                end_dt = self._parse_datetime(end_time)
                if end_dt:
                    time_filter["$lte"] = end_dt
            
            if time_filter:
                filter_dict["timestamp"] = time_filter
            
            # 执行查询
            cursor = collection.find(filter_dict).sort("timestamp", DESCENDING).limit(limit)
            logs = list(cursor)
            
            # 转换 ObjectId 为字符串
            for log in logs:
                if "_id" in log:
                    log["_id"] = str(log["_id"])
                if "timestamp" in log:
                    log["timestamp"] = log["timestamp"].isoformat()
            
            self.logger.info(f"查询 API 日志: 过滤器={filter_dict}, 返回 {len(logs)} 条记录")
            return logs
            
        except Exception as e:
            self.logger.error(f"查询 API 日志失败: {e}")
            return []
    
    def query_error_logs(
        self,
        user_id: Optional[int] = None,
        error_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查询错误日志
        
        Args:
            user_id: 用户 ID
            error_type: 错误类型
            start_time: 开始时间
            end_time: 结束时间
            limit: 结果数量限制
            
        Returns:
            错误日志列表
        """
        try:
            collection = self.get_logs_collection()
            if collection is None:
                return []
            
            filter_dict = {"status": {"$gte": 400}}  # 只查询状态码 >= 400 的日志
            
            if user_id:
                filter_dict["user_id"] = user_id
            
            if error_type:
                filter_dict["error_type"] = error_type
            
            # 处理时间过滤
            time_filter = {}
            if start_time:
                start_dt = self._parse_datetime(start_time)
                if start_dt:
                    time_filter["$gte"] = start_dt
            
            if end_time:
                end_dt = self._parse_datetime(end_time)
                if end_dt:
                    time_filter["$lte"] = end_dt
            
            if time_filter:
                filter_dict["timestamp"] = time_filter
            
            # 执行查询
            cursor = collection.find(filter_dict).sort("timestamp", DESCENDING).limit(limit)
            logs = list(cursor)
            
            # 转换 ObjectId 为字符串
            for log in logs:
                if "_id" in log:
                    log["_id"] = str(log["_id"])
                if "timestamp" in log:
                    log["timestamp"] = log["timestamp"].isoformat()
            
            self.logger.info(f"查询错误日志: 返回 {len(logs)} 条记录")
            return logs
            
        except Exception as e:
            self.logger.error(f"查询错误日志失败: {e}")
            return []
    
    def get_user_activity_stats(
        self,
        user_id: int,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户活动统计
        
        Args:
            user_id: 用户 ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计信息字典
        """
        try:
            collection = self.get_logs_collection()
            if collection is None:
                return {}
            
            filter_dict = {"user_id": user_id}
            
            # 处理时间过滤
            time_filter = {}
            if start_time:
                start_dt = self._parse_datetime(start_time)
                if start_dt:
                    time_filter["$gte"] = start_dt
            
            if end_time:
                end_dt = self._parse_datetime(end_time)
                if end_dt:
                    time_filter["$lte"] = end_dt
            
            if time_filter:
                filter_dict["timestamp"] = time_filter
            
            # 统计总请求数
            total_requests = collection.count_documents(filter_dict)
            
            # 统计各 HTTP 方法的请求数
            method_stats = list(collection.aggregate([
                {"$match": filter_dict},
                {"$group": {"_id": "$method", "count": {"$sum": 1}}}
            ]))
            
            # 统计各路径的请求数
            path_stats = list(collection.aggregate([
                {"$match": filter_dict},
                {"$group": {"_id": "$path", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]))
            
            # 统计错误数
            error_count = collection.count_documents({**filter_dict, "status": {"$gte": 400}})
            
            stats = {
                "user_id": user_id,
                "total_requests": total_requests,
                "error_count": error_count,
                "method_distribution": {item["_id"]: item["count"] for item in method_stats},
                "top_paths": [{"path": item["_id"], "count": item["count"]} for item in path_stats]
            }
            
            self.logger.info(f"获取用户 {user_id} 的活动统计: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"获取用户活动统计失败: {e}")
            return {}
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """
        解析日期时间字符串
        
        支持格式:
        - ISO 格式: "2024-01-01T12:00:00"
        - 相对时间: "1h", "2d", "1w" (h=小时, d=天, w=周)
        
        Args:
            datetime_str: 日期时间字符串
            
        Returns:
            datetime 对象或 None
        """
        try:
            # 尝试解析 ISO 格式
            if "T" in datetime_str or "-" in datetime_str:
                return datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            
            # 解析相对时间
            if datetime_str.endswith("h"):
                hours = int(datetime_str[:-1])
                return datetime.utcnow() - timedelta(hours=hours)
            elif datetime_str.endswith("d"):
                days = int(datetime_str[:-1])
                return datetime.utcnow() - timedelta(days=days)
            elif datetime_str.endswith("w"):
                weeks = int(datetime_str[:-1])
                return datetime.utcnow() - timedelta(weeks=weeks)
            
            return None
        except Exception as e:
            self.logger.error(f"解析日期时间 '{datetime_str}' 失败: {e}")
            return None
    
    def get_langchain_tools(self):
        """获取 LangChain 格式的工具列表"""
        
        # 保存对象引用，以便在嵌套函数中使用
        db_tools = self
        
        @tool
        def list_mongodb_collections() -> str:
            """
            列出 MongoDB 数据库中的所有 collection 及其基本信息。
            这个工具可以帮助你了解有哪些数据集合可以查询。
            
            Returns:
                JSON 格式的 collection 列表和每个 collection 中的记录数
            """
            try:
                collections_info = []
                for collection_name in db_tools.db.list_collection_names():
                    try:
                        collection = db_tools.db[collection_name]
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
                        db_tools.logger.warning(f"无法获取 {collection_name} 的信息: {e}")
                        collections_info.append({
                            "name": collection_name,
                            "error": str(e)
                        })
                
                return json.dumps(collections_info, ensure_ascii=False, indent=2)
            except Exception as e:
                error_msg = f"获取 collection 列表失败: {str(e)}"
                db_tools.logger.error(error_msg)
                return error_msg
        
        @tool
        def query_mongodb(query_params: str) -> str:
            """
            通用的 MongoDB 查询工具，可以查询任意 collection。
            
            Args:
                query_params: JSON 格式的查询参数字符串，包含以下字段：
                    - collection_name (必需): collection 的名称，如 "api_logs", "error_logs", "articlelogs" 等
                    - filter_dict (可选): JSON 格式的查询条件，如 {"user_id": 122} 或 {"status": {"$gte": 400}}
                    - limit (可选): 返回结果数量限制，默认 10
                
                示例: '{"collection_name": "api_logs", "limit": 10}' 或 '{"collection_name": "api_logs", "filter_dict": {"user_id": 122}, "limit": 20}'
                
            Returns:
                JSON 格式的查询结果
            """
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
                    return "错误: 必须提供 collection_name 参数"
                
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
                collection = db_tools.db[collection_name]
                
                # 执行查询
                cursor = collection.find(filter_obj).limit(limit_int)
                results = []
                for doc in cursor:
                    # 转换所有 datetime 对象为 ISO 格式字符串
                    doc = db_tools._convert_datetime_to_string(doc)
                    results.append(doc)
                
                db_tools.logger.info(f"查询 {collection_name}: 条件={filter_obj}, 返回 {len(results)} 条记录")
                return json.dumps(results, ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"MongoDB 查询失败: {str(e)}"
                db_tools.logger.error(error_msg)
                return error_msg
        
        return [list_mongodb_collections, query_mongodb]
    
    def _convert_datetime_to_string(self, obj):
        """递归转换所有 datetime 对象为 ISO 格式字符串"""
        
        if isinstance(obj, dict):
            # 处理字典中的所有值
            result = {}
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
    
    def _format_results(self, results) -> str:
        """将结果格式化为字符串"""
        try:
            return json.dumps(results, ensure_ascii=False, indent=2)
        except:
            return str(results)


def get_mongodb_tools() -> MongoDBTools:
    """获取 MongoDB 日志工具实例"""
    return MongoDBTools()
