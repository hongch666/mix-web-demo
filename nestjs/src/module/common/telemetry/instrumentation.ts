import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { PrometheusExporter } from "@opentelemetry/exporter-prometheus";
import { NodeSDK } from "@opentelemetry/sdk-node";
import {
  AlwaysOffSampler,
  AlwaysOnSampler,
  ParentBasedSampler,
  type Sampler,
  TraceIdRatioBasedSampler,
} from "@opentelemetry/sdk-trace-base";
import { Messages, TelemetryConstants } from "src/common/constants";
import config from "src/config";

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

function createRatioSampler(ratioValue: string): TraceIdRatioBasedSampler {
  const ratio: number = Number(ratioValue);
  if (!Number.isFinite(ratio) || ratio < 0 || ratio > 1) {
    throw new Error(Messages.OTEL_INVALID_SAMPLER_RATIO(ratioValue));
  }
  return new TraceIdRatioBasedSampler(ratio);
}

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
      metricReader: new PrometheusExporter({
        port: Number(telemetryConfig.metricsPort),
        endpoint: telemetryConfig.metricsEndpoint,
      }),
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

export async function shutdownTelemetry(): Promise<void> {
  await telemetrySdk?.shutdown();
}
