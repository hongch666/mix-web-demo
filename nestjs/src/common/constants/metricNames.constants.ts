/**
 * Prometheus 监控指标名称常量集合，涵盖 HTTP 请求、客户端请求与定时任务等指标
 */
export class MetricNames {
  // ===== 监控指标名称 =====

  /** HTTP 请求量计数器 */
  static readonly HTTP_REQUESTS = "mix_http_requests_total";
  /** HTTP 请求耗时直方图 */
  static readonly HTTP_DURATION = "mix_http_request_duration_seconds";
  /** 服务间调用量计数器 */
  static readonly CLIENT_REQUESTS = "mix_client_requests_total";
  /** 服务间调用耗时直方图 */
  static readonly CLIENT_DURATION = "mix_client_request_duration_seconds";
  /** 定时任务执行次数计数器 */
  static readonly TASK_RUNS = "mix_task_runs_total";
  /** 定时任务执行耗时直方图 */
  static readonly TASK_DURATION = "mix_task_duration_seconds";
}
