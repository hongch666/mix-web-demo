/**
 * OpenTelemetry 遥测配置结构，包含开关、服务名、链路上报地址、采样器及指标服务端口与路径
 */
export interface TelemetryConfig {
  enabled: boolean;
  serviceName: string;
  tracesEndpoint: string;
  sampler: string;
  samplerArg: string;
  metricsPort: number;
  metricsEndpoint: string;
}
