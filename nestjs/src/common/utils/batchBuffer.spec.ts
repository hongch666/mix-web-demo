import { BatchBuffer } from "./batchBuffer";

describe("BatchBuffer", () => {
  const createLogger = () => ({
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const logger = createLogger();
    const flushed: number[][] = [];
    const buffer = new BatchBuffer<number>(
      "numbers",
      { batchSize: 2, maxBufferSize: 10 },
      async (batch) => {
        flushed.push(batch);
      },
      logger as never,
    );

    buffer.enqueue(1);
    buffer.enqueue(2);
    await new Promise<void>((resolve) => setImmediate(resolve));

    expect(flushed).toEqual([[1, 2]]);
    expect(buffer.size).toBe(0);
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const logger = createLogger();
    const flushed: string[][] = [];
    let attempts = 0;
    const buffer = new BatchBuffer<string>(
      "events",
      // Verify the expected behavior of this unit test
      { batchSize: 10, maxBufferSize: 10, maxRetries: 1 },
      async (batch) => {
        attempts += 1;
        if (attempts === 1) throw new Error("temporary failure");
        flushed.push(batch);
      },
      logger as never,
    );

    buffer.enqueue("first");
    await buffer.flush();
    expect(logger.error).toHaveBeenCalled();
    expect(buffer.size).toBe(0);

    buffer.enqueue("second");
    await buffer.shutdown();
    expect(flushed).toEqual([["second"]]);
    expect(buffer.size).toBe(0);

    buffer.enqueue("discarded");
    expect(buffer.size).toBe(0);
    expect(logger.warning).toHaveBeenCalled();
  });
});
