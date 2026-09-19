import { Module } from "@nestjs/common";

import { TelemetryLifecycleService } from "./telemetry.lifecycle.service";

@Module({
  providers: [TelemetryLifecycleService],
})
export class TelemetryModule {}
