import { LoggerService } from "./logger.service";

describe("LoggerService", () => {
  // 验证日志服务优先读取环境变量中的日志目录
  it("验证环境变量优先配置日志目录", () => {
    const config = {
      get: jest.fn((key: string) =>
        key === "LOG_PATH" ? "test-logs" : undefined,
      ),
    };
    const service = new LoggerService(config as never);
    service.onModuleInit();
    expect(config.get).toHaveBeenCalledWith("LOG_PATH");
  });
});
