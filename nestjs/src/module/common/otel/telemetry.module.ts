import { Module } from "@nestjs/common";

import { TelemetryLifecycleService } from "./telemetryLifecycle.service";

@Module({
  providers: [TelemetryLifecycleService],
})
export class TelemetryModule {}
