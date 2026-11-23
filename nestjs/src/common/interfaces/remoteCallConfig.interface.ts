/**
 * 远程调用配置，包含超时、重试与指数退避参数及熔断器各项阈值
 */
export interface RemoteCallConfig {
  timeout: number;
  maxRetries: number;
  initialBackoff: number;
  maxBackoff: number;
  circuitBreaker: {
    timeout: number;
    errorThresholdPercentage: number;
    resetTimeout: number;
    volumeThreshold: number;
  };
}
