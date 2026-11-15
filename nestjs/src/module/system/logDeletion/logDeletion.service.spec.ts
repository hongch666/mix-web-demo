import { LogDeletionService } from "./logDeletion.service";

/**
 * 构造墓碑服务实例，索引初始化、模型与日志全部替换为替身
 * @param findResult 游标查询返回的文档
 */
function createService(findResult: Array<Record<string, unknown>> = []): {
  service: LogDeletionService;
  insertMany: jest.Mock;
  find: jest.Mock;
} {
  const insertMany = jest.fn().mockResolvedValue([]);
  const find = jest.fn().mockReturnValue({
    sort: jest.fn().mockReturnValue({
      limit: jest.fn().mockReturnValue({
        lean: jest.fn().mockReturnValue({
          exec: jest.fn().mockResolvedValue(findResult),
        }),
      }),
    }),
  });
  const logDeletionModel = {
    collection: {
      getIndexes: jest.fn().mockResolvedValue([]),
      createIndex: jest.fn().mockResolvedValue("created"),
    },
    insertMany,
    find,
  };
  const logger = { info: jest.fn(), error: jest.fn(), warning: jest.fn() };
  const service = new LogDeletionService(
    logDeletionModel as never,
    logger as never,
  );
  return { service, insertMany, find };
}

describe("LogDeletionService.recordDeletions", () => {
  // 验证墓碑按日志类型与主键记录，并带上原日志产生时间供数仓定位分区
  it("验证按日志类型记录墓碑", async () => {
    const { service, insertMany } = createService();
    const createdAt: Date = new Date("2026-01-01T00:00:00Z");

    await service.recordDeletions("api", [{ id: "id-1", createdAt }]);

    expect(insertMany).toHaveBeenCalledWith(
      [{ logType: "api", eventId: "id-1", logCreatedAt: createdAt }],
      { ordered: false },
    );
  });

  // 验证没有待删日志时不产生任何写入
  it("验证空列表不写入墓碑", async () => {
    const { service, insertMany } = createService();

    await service.recordDeletions("article", []);

    expect(insertMany).not.toHaveBeenCalled();
  });

  // 验证同一日志重复删除引发的主键冲突被忽略，删除流程继续
  it("验证主键冲突被忽略", async () => {
    const { service, insertMany } = createService();
    insertMany.mockRejectedValueOnce(
      Object.assign(new Error("duplicate key"), {
        writeErrors: [{ code: 11000 }],
      }),
    );

    await expect(
      service.recordDeletions("api", [{ id: "id-1" }]),
    ).resolves.toBeUndefined();
  });

  // 验证非主键冲突的写入失败继续抛出，避免删除无法传播到数仓
  it("验证其它写入失败继续抛出", async () => {
    const { service, insertMany } = createService();
    insertMany.mockRejectedValueOnce(new Error("connection lost"));

    await expect(
      service.recordDeletions("api", [{ id: "id-1" }]),
    ).rejects.toThrow("connection lost");
  });
});

describe("LogDeletionService.findByCursor", () => {
  // 验证游标查询按主键升序返回墓碑，时间按业务时区格式化
  it("验证游标查询返回墓碑并格式化时间", async () => {
    const { service } = createService([
      {
        _id: "651f1a2b3c4d5e6f708192a3",
        logType: "api",
        eventId: "event-1",
        logCreatedAt: new Date("2026-01-01T00:00:00Z"),
      },
    ]);

    const page = await service.findByCursor(null, 1000);

    expect(page.list).toEqual([
      {
        _id: "651f1a2b3c4d5e6f708192a3",
        logType: "api",
        eventId: "event-1",
        logCreatedAt: "2026-01-01 08:00:00",
      },
    ]);
    expect(page.nextCursor).toBeNull();
  });

  // 验证还有更多数据时返回最后一个墓碑 ID 作为下一页游标
  it("验证多页时返回下一页游标", async () => {
    const { service } = createService([
      { _id: "651f1a2b3c4d5e6f708192a3", logType: "api", eventId: "event-1" },
      {
        _id: "651f1a2b3c4d5e6f708192a4",
        logType: "article",
        eventId: "event-2",
      },
    ]);

    const page = await service.findByCursor(null, 1);

    expect(page.list).toHaveLength(1);
    expect(page.nextCursor).toBe("651f1a2b3c4d5e6f708192a3");
  });
});
