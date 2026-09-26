import { LogConsumerService } from "./articleLog.consume.service";

describe("LogConsumerService", () => {
  // 验证缺少操作类型的文章日志消息不会入库
  it("验证缺少操作类型的消息被忽略", async () => {
    const insertMany = jest.fn();
    const service = new LogConsumerService(
      { insertMany } as never,
      { info: jest.fn(), error: jest.fn(), warning: jest.fn() } as never,
    );
    await service.handleArticleLog({ content: { title: "文章" } });
    await service.flushPendingLogs();
    expect(insertMany).not.toHaveBeenCalled();
  });
});
