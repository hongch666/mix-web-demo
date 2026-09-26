import { ApiLogConsumerService } from "./apiLog.consume.service";

describe("ApiLogConsumerService", () => {
  // 验证无效接口日志消息不会写入数据库
  it("验证无效消息被忽略", async () => {
    const insertMany = jest.fn();
    const service = new ApiLogConsumerService(
      { insertMany } as never,
      { info: jest.fn(), error: jest.fn(), warning: jest.fn() } as never,
    );
    await service.handleApiLog({ userId: 1 });
    await service.flushPendingLogs();
    expect(insertMany).not.toHaveBeenCalled();
  });
});
