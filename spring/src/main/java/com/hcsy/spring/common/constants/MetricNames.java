package com.hcsy.spring.common.constants;

public final class MetricNames {

    private MetricNames() {
    }

    public static final String CLIENT_REQUESTS = "mix_client_requests_total";
    public static final String CLIENT_DURATION = "mix_client_request_duration_seconds";
    public static final String TASK_RUNS = "mix_task_runs_total";
    public static final String TASK_DURATION = "mix_task_duration_seconds";
    public static final String USER_LOGIN = "mix_user_login_total";
    public static final String USER_REGISTER = "mix_user_register_total";
}
