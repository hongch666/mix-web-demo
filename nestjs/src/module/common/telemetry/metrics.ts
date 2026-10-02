import {
  collectDefaultMetrics,
  Counter,
  Histogram,
  Registry,
} from "prom-client";
import { MetricNames } from "src/common/constants";

export const metricsRegistry: Registry = new Registry();

collectDefaultMetrics({ register: metricsRegistry });

export const httpRequests: Counter<string> = new Counter({
  name: MetricNames.HTTP_REQUESTS,
  help: "HTTP 请求次数",
  labelNames: ["method", "route", "status"],
  registers: [metricsRegistry],
});

export const httpDuration: Histogram<string> = new Histogram({
  name: MetricNames.HTTP_DURATION,
  help: "HTTP 请求耗时",
  labelNames: ["method", "route"],
  registers: [metricsRegistry],
});

export const clientRequests: Counter<string> = new Counter({
  name: MetricNames.CLIENT_REQUESTS,
  help: "下游服务调用次数",
  labelNames: ["target_service", "method", "outcome"],
  registers: [metricsRegistry],
});

export const clientDuration: Histogram<string> = new Histogram({
  name: MetricNames.CLIENT_DURATION,
  help: "下游服务调用耗时",
  labelNames: ["target_service", "method"],
  registers: [metricsRegistry],
});

export const taskRuns: Counter<string> = new Counter({
  name: MetricNames.TASK_RUNS,
  help: "定时任务执行次数",
  labelNames: ["task", "result"],
  registers: [metricsRegistry],
});

export const taskDuration: Histogram<string> = new Histogram({
  name: MetricNames.TASK_DURATION,
  help: "定时任务执行耗时",
  labelNames: ["task"],
  registers: [metricsRegistry],
});
