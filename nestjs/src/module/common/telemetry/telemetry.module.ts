import { Module } from "@nestjs/common";

import { TelemetryLifecycleService } from "./telemetry.lifecycle.service";

/**
 * 遥测模块，注册遥测生命周期服务以在应用停机时释放遥测资源
 */
@Module({
  providers: [TelemetryLifecycleService],
})
export class TelemetryModule {}
