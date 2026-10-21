import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { NodeSDK } from "@opentelemetry/sdk-node";
import type { Server } from "node:http";
import {
  AlwaysOffSampler,
  AlwaysOnSampler,
  ParentBasedSampler,
  type Sampler,
  TraceIdRatioBasedSampler,
} from "@opentelemetry/sdk-trace-base";
import { Messages, TelemetryConstants } from "src/common/constants";
import config from "src/config";
import { startMetricsServer } from "./metrics.server";

/**
 * OpenTelemetry 遥测配置结构，包含开关、服务名、链路上报地址、采样器及指标服务端口与路径
 */
interface TelemetryConfig {
  enabled: boolean;
  serviceName: string;
  tracesEndpoint: string;
  sampler: string;
  samplerArg: string;
  metricsPort: number;
  metricsEndpoint: string;
}

const telemetryConfig: TelemetryConfig = config.telemetry as TelemetryConfig;
let metricsServer: Server | undefined;

/**
 * 根据传入比例值创建基于 TraceId 的比例采样器，比例非法时抛出错误
 */
function createRatioSampler(ratioValue: string): TraceIdRatioBasedSampler {
  const ratio: number = Number(ratioValue);
  if (!Number.isFinite(ratio) || ratio < 0 || ratio > 1) {
    throw new Error(Messages.OTEL_INVALID_SAMPLER_RATIO(ratioValue));
  }
  return new TraceIdRatioBasedSampler(ratio);
}

/**
 * 按配置中的采样器名称创建对应的 OpenTelemetry 采样器实例，不支持的名称抛出错误
 */
function createSampler(telemetry: TelemetryConfig): Sampler {
  switch (telemetry.sampler) {
    case TelemetryConstants.SAMPLER_ALWAYS_ON:
      return new AlwaysOnSampler();
    case TelemetryConstants.SAMPLER_ALWAYS_OFF:
      return new AlwaysOffSampler();
    case TelemetryConstants.SAMPLER_TRACE_ID_RATIO:
      return createRatioSampler(telemetry.samplerArg);
    case TelemetryConstants.SAMPLER_PARENT_ALWAYS_ON:
      return new ParentBasedSampler({ root: new AlwaysOnSampler() });
    case TelemetryConstants.SAMPLER_PARENT_ALWAYS_OFF:
      return new ParentBasedSampler({ root: new AlwaysOffSampler() });
    case TelemetryConstants.SAMPLER_PARENT_TRACE_ID_RATIO:
      return new ParentBasedSampler({
        root: createRatioSampler(telemetry.samplerArg),
      });
    default:
      throw new Error(Messages.OTEL_UNSUPPORTED_SAMPLER(telemetry.sampler));
  }
}

const telemetrySdk: NodeSDK | undefined = telemetryConfig.enabled
  ? new NodeSDK({
      serviceName: telemetryConfig.serviceName,
      sampler: createSampler(telemetryConfig),
      traceExporter: new OTLPTraceExporter({
        url: telemetryConfig.tracesEndpoint,
      }),
      instrumentations: [
        getNodeAutoInstrumentations({
          "@opentelemetry/instrumentation-fs": { enabled: false },
        }),
      ],
    })
  : undefined;

telemetrySdk?.start();
if (telemetryConfig.enabled) {
  metricsServer = startMetricsServer(
    Number(telemetryConfig.metricsPort),
    telemetryConfig.metricsEndpoint,
  );
}

/**
 * 关闭遥测 SDK 并停止指标暴露的 HTTP 服务，用于应用优雅停机
 */
export async function shutdownTelemetry(): Promise<void> {
  await telemetrySdk?.shutdown();
  if (metricsServer) {
    await new Promise<void>((resolve, reject) => {
      metricsServer?.close((error?: Error) => {
        if (error) {
          reject(error);
          return;
        }
        resolve();
      });
    });
  }
}
