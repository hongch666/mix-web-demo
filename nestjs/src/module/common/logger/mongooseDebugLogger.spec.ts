import type { LoggerService } from "./logger.service";
import { createMongooseDebugLogger } from "./mongooseDebugLogger";

describe("createMongooseDebugLogger", () => {
  const createLogger = (): {
    logger: LoggerService;
    debugMock: jest.Mock;
  } => {
    const debugMock = jest.fn();
    const logger = { debug: debugMock } as unknown as LoggerService;
    return { logger, debugMock };
  };

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // 验证该测试场景的预期行为
  it("格式化集合名方法名与参数后输出到统一日志服务", () => {
    const { logger, debugMock } = createLogger();
    const debugLogger = createMongooseDebugLogger(logger);

    debugLogger("apilogs", "find", { createdAt: { $gte: 1 } }, { limit: 10 });

    expect(debugMock).toHaveBeenCalledWith(
      "Mongoose: apilogs.find({ createdAt: { '$gte': 1 } }, { limit: 10 })",
    );
  });

  // 验证该测试场景的预期行为
  it("Buffer 与循环引用参数序列化不抛错", () => {
    const { logger, debugMock } = createLogger();
    const debugLogger = createMongooseDebugLogger(logger);
    const circular: Record<string, unknown> = { name: "pipeline" };
    circular["self"] = circular;

    expect(() =>
      debugLogger("articlelogs", "insertMany", Buffer.from("doc"), circular),
    ).not.toThrow();

    const message = debugMock.mock.calls[0]?.[0] as string;
    expect(message).toContain("Mongoose: articlelogs.insertMany(");
    expect(message).toContain("pipeline");
  });

  // 验证该测试场景的预期行为
  it("无参数时输出空参数列表", () => {
    const { logger, debugMock } = createLogger();
    const debugLogger = createMongooseDebugLogger(logger);

    debugLogger("apilogs", "estimatedDocumentCount");

    expect(debugMock).toHaveBeenCalledWith(
      "Mongoose: apilogs.estimatedDocumentCount()",
    );
  });
});
