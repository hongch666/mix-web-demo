import { Injectable, OnApplicationShutdown } from "@nestjs/common";

import { shutdownTelemetry } from "./instrumentation";

/**
 * 遥测生命周期服务，在应用关闭钩子中负责停机时关闭遥测资源
 */
@Injectable()
export class TelemetryLifecycleService implements OnApplicationShutdown {
  /**
   * 应用关闭时调用 shutdownTelemetry 停止遥测 SDK 与指标服务
   */
  async onApplicationShutdown(): Promise<void> {
    await shutdownTelemetry();
  }
}
