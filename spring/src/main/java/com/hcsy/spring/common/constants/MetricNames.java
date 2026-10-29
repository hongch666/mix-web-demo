package com.hcsy.spring.common.constants;

/**
 * 聚合 Micrometer 监控指标名称常量
 */
public final class MetricNames {

    /**
     * 聚合 Micrometer 监控指标名称常量
     */
    private MetricNames() {
    }

    // ===== 监控指标名称 =====

    /** 服务间调用量计数器 */
    public static final String CLIENT_REQUESTS = "mix_client_requests_total";
    /** 服务间调用耗时直方图 */
    public static final String CLIENT_DURATION = "mix_client_request_duration_seconds";
    /** 定时任务执行次数计数器 */
    public static final String TASK_RUNS = "mix_task_runs_total";
    /** 定时任务执行耗时直方图 */
    public static final String TASK_DURATION = "mix_task_duration_seconds";
    /** 用户登录次数计数器 */
    public static final String USER_LOGIN = "mix_user_login_total";
    /** 用户注册次数计数器 */
    public static final String USER_REGISTER = "mix_user_register_total";
}
