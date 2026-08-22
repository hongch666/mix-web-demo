package com.hcsy.gateway.common.constants;

/**
 * 消息类常量
 * 集中管理日志描述、异常提示、接口返回的中文消息，避免业务代码中硬编码字符串
 */
public class Messages {

    private Messages() {
    }

    // ===== 鉴权/令牌 =====
    public static final String TOKEN_TYPE_ERROR = "Token类型错误";
    public static final String TOKEN_EXPIRED_MSG = "Token已过期";
    public static final String TOKEN_INVALID_MSG = "无效的Token";

    public static final String USER_NOT_LOGIN = "用户未登录，请先登录";
    public static final String SERVICE_TEMP_UNAVAILABLE = "服务暂时不可用，请稍后重试";
    public static final String SERVER_INTERNAL_ERROR = "服务器内部错误，请稍后重试";

    // ===== 限流 =====
    public static final String RATELIMIT_BUCKET_EXEC_ERROR = "限流器执行出错: key={}, Redis异常，拒绝请求";
    public static final String RATELIMIT_STATUS_ERROR = "获取限流器状态出错: key={}";
    public static final String RATELIMIT_RESET_SUCCESS = "已重置限流器: key={}, capacity={}";
    public static final String RATELIMIT_RESET_FAIL = "重置限流器失败: key={}";
    public static final String RATELIMIT_CHECK_PASS = "限流检查通过: key={}, 剩余令牌数={}";
    public static final String RATELIMIT_REJECTED = "请求被限流: key={}, 剩余令牌数={}";

    public static final String RATELIMIT_FILTER_REJECTED = "[{}] 请求被限流: path={}, clientId={}";
    public static final String RATELIMIT_FILTER_PASS = "[{}] 限流检查通过: path={}, clientId={}";

    // ===== 内部接口拦截 =====
    public static final String EXCLUDE_INTERCEPT_PATH = "排除列表拦截路径: {}";
    public static final String INTERNAL_INTERFACE_FORBIDDEN = "该接口为内部接口，仅内部使用";

    // ===== 鉴权过滤器日志 =====
    public static final String AUTH_EXCLUDE_PATH = "排除身份验证的路径: {}";
    public static final String AUTH_SUCCESS = "身份验证成功 - 用户ID: {}, 路径: {}";
    public static final String AUTH_FAIL = "[{}] 认证失败 - 路径: {}";
    public static final String AUTH_UNEXPECTED_ERROR = "[{}] 认证流程非预期异常 - 路径: {}";
    public static final String REDIS_UNAVAILABLE_AUTH_INTERRUPT = "[{}] Redis 不可用，认证流程中断 - 路径: {}";

    // ===== 网关异常处理 =====
    public static final String NO_AVAILABLE_SERVICE_INSTANCE = "找不到可用的服务实例: %s";
    public static final String SERVICE_UNAVAILABLE = "服务不可用";
    public static final String SERVICE_CALL_FAILED = "服务调用失败";
    public static final String REQUEST_TIMEOUT = "请求超时，请稍后重试";

    // ===== 结果序列化 =====
    public static final String RESULT_SERIALIZE_FAIL = "序列化响应结果失败";

    // ===== 配置加载 =====
    public static final String DOTENV_NOT_EXIST = "[DotenvLoader] .env文件不存在，跳过加载";
    public static final String DOTENV_LOADED = "[DotenvLoader] 成功加载 {} 个环境变量";
    public static final String DOTENV_LOAD_FAIL = "[DotenvLoader] 加载.env文件失败: ";

    // ===== Redis 连接 =====
    public static final String REDIS_USERNAME = "[Redis] 用户名: {}";
    public static final String REDIS_PASSWORD_SET = "[Redis] 已设置密码";
    public static final String REDIS_CONNECT = "[Redis] 连接: {}:{}, DB: {}";

    // ===== Swagger 资源 =====
    public static final String SWAGGER_UI_RESOURCE_NOT_EXIST = "Swagger UI 资源不存在: {}";
    public static final String SWAGGER_UI_RESOURCE_READ_FAIL = "读取 Swagger UI 资源失败: {}";
}
