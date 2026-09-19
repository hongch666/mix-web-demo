import { Injectable, OnApplicationShutdown } from "@nestjs/common";

import { shutdownTelemetry } from "./instrumentation";

@Injectable()
export class TelemetryLifecycleService implements OnApplicationShutdown {
  async onApplicationShutdown(): Promise<void> {
    await shutdownTelemetry();
  }
}
