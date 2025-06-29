import oss2
from common.utils.writeLog import fileLogger as logger
from config.config import load_config, load_secret_config

# 配置你的阿里云OSS信息
access_key_id: str = load_secret_config("oss")["access_key_id"]
access_key_secret: str = load_secret_config("oss")["access_key_secret"]
bucket_name: str = load_config("oss")["bucket_name"]
endpoint: str = load_config("oss")["endpoint"]

class OSSClient:
    auth: oss2.Auth
    bucket_name: str
    endpoint: str
    bucket: oss2.Bucket

    def __init__(self) -> None:
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)

    def upload_file(self, local_file: str, oss_file: str) -> str:
        """上传本地文件到OSS，返回OSS文件URL"""
        logger.info("开始上传文件到OSS")
        self.bucket.put_object_from_file(oss_file, local_file)
        logger.info(f"文件上传成功: {oss_file}")
        # 返回文件的公网访问地址
        return self.get_file_url(oss_file)

    def get_file_url(self, oss_file: str) -> str:
        """获取OSS文件公网访问地址"""
        return f"https://{self.bucket_name}.{self.endpoint}/{oss_file}"