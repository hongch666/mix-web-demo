jest.mock("./instrumentation", () => ({
  shutdownTelemetry: jest.fn().mockResolvedValue(undefined),
}));

import { shutdownTelemetry } from "./instrumentation";
import { TelemetryLifecycleService } from "./telemetry.lifecycle.service";

describe("TelemetryLifecycleService", () => {
  // 验证应用关闭时释放遥测资源
  it("验证应用关闭时释放遥测资源", async () => {
    await new TelemetryLifecycleService().onApplicationShutdown();
    expect(shutdownTelemetry).toHaveBeenCalled();
  });
});
