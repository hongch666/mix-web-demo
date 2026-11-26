/* eslint-disable @typescript-eslint/no-explicit-any */
import { OssObjectRecord, OssObjectService } from "./ossObject.service";

const PREFIX = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/";

const RECORD: OssObjectRecord = {
  ossKey: "pic/a.png",
  ossUrl: PREFIX + "pic/a.png",
  prefixType: "pic",
  source: "user_image",
  uploaderUserId: 7,
};

/**
 * 构造查询构建器桩，按调用链返回自身并在终点返回 preset
 */
function queryBuilder(
  preset: {
    execute?: unknown;
    raw?: unknown[];
  } = {},
) {
  const qb: any = {
    insert: jest.fn(() => qb),
    into: jest.fn(() => qb),
    values: jest.fn(() => qb),
    orIgnore: jest.fn(() => qb),
    select: jest.fn(() => qb),
    where: jest.fn(() => qb),
    andWhere: jest.fn(() => qb),
    update: jest.fn(() => qb),
    set: jest.fn(() => qb),
    execute: jest
      .fn()
      .mockResolvedValue(preset.execute ?? { generatedMaps: [] }),
    getRawMany: jest.fn().mockResolvedValue(preset.raw ?? []),
  };
  return qb;
}

/**
 * 构造仅验证账本读写的服务实例，清理依赖用空桩
 */
function buildLedgerService(
  qb: any,
  removeResult: { affected?: number } = { affected: 1 },
) {
  const repository = {
    createQueryBuilder: jest.fn(() => qb),
    delete: jest.fn().mockResolvedValue(removeResult),
  };
  const service = new OssObjectService(
    repository as never,
    {} as never,
    {} as never,
    {} as never,
    { info: jest.fn(), warning: jest.fn(), error: jest.fn() } as never,
  );
  return { service, repository };
}

describe("OssObjectService 账本读写", () => {
  // 登记新对象时 generatedMaps 非空返回 true，并正确写入字段
  it("登记新对象返回 true 并写入字段", async () => {
    const qb = queryBuilder({ execute: { generatedMaps: [{ id: 1 }] } });
    const { service } = buildLedgerService(qb);

    await expect(service.register(RECORD)).resolves.toBe(true);
    expect(qb.values).toHaveBeenCalledWith(
      expect.objectContaining({
        oss_key: "pic/a.png",
        source: "user_image",
        uploader_user_id: 7,
        file_size: null,
      }),
    );
  });

  // 唯一键冲突被忽略时 generatedMaps 为空返回 false
  it("登记已存在对象返回 false", async () => {
    const qb = queryBuilder({ execute: { generatedMaps: [] } });
    const { service } = buildLedgerService(qb);

    await expect(service.register(RECORD)).resolves.toBe(false);
  });

  // 空补录列表直接返回 0，不访问 Repository
  it("空补录列表返回 0 且不查库", async () => {
    const { service, repository } = buildLedgerService(queryBuilder());

    await expect(service.backfill([])).resolves.toBe(0);
    expect(repository.createQueryBuilder).not.toHaveBeenCalled();
  });

  // 批量补录返回实际写入条数，并带上 last_verified_at
  it("批量补录返回写入条数并标记核验时间", async () => {
    const qb = queryBuilder({
      execute: { generatedMaps: [{ id: 1 }, { id: 2 }] },
    });
    const { service } = buildLedgerService(qb);

    const count = await service.backfill([
      RECORD,
      { ...RECORD, ossKey: "pic/b.png" },
    ]);

    expect(count).toBe(2);
    const values = qb.values.mock.calls[0]![0] as Array<
      Record<string, unknown>
    >;
    expect(values).toHaveLength(2);
    expect(values[0]).toHaveProperty("last_verified_at");
  });

  // 查询全部 key 时映射 oss_key 列
  it("查询全部 key 映射 oss_key 列", async () => {
    const qb = queryBuilder({
      raw: [{ oss_key: "pic/a.png" }, { oss_key: "pdf/g.pdf" }],
    });
    const { service } = buildLedgerService(qb);

    await expect(service.listAllKeys()).resolves.toEqual([
      "pic/a.png",
      "pdf/g.pdf",
    ]);
  });

  // 宽限期查询按 key 前缀匹配并传入 cutoff，空前缀返回空且不查库
  it("宽限期查询按 key 前缀匹配 cutoff，空前缀直接返回空", async () => {
    const qb = queryBuilder({ raw: [{ oss_key: "pic/a.png" }] });
    const { service, repository } = buildLedgerService(qb);
    const cutoff = new Date("2026-01-01T00:00:00Z");

    await expect(
      service.listKeysOlderThan(cutoff, ["pic/", "pdf/"]),
    ).resolves.toEqual(["pic/a.png"]);
    expect(qb.where).toHaveBeenCalledWith("obj.create_at < :cutoff", {
      cutoff,
    });
    expect(qb.andWhere).toHaveBeenCalledWith(
      "(obj.oss_key LIKE :prefix0 OR obj.oss_key LIKE :prefix1)",
      {
        prefix0: "pic/%",
        prefix1: "pdf/%",
      },
    );

    await expect(service.listKeysOlderThan(cutoff, [])).resolves.toEqual([]);
    expect(repository.createQueryBuilder).toHaveBeenCalledTimes(1);
  });

  // 空 key 列表 markVerified 与 removeByKeys 直接返回，不查库
  it("空 key 列表的标记与删除均不查库", async () => {
    const { service, repository } = buildLedgerService(queryBuilder());

    await service.markVerified([], new Date());
    await expect(service.removeByKeys([])).resolves.toBe(0);
    expect(repository.createQueryBuilder).not.toHaveBeenCalled();
    expect(repository.delete).not.toHaveBeenCalled();
  });
});

/**
 * 构造清理场景的服务实例；repository 的 getRawMany 以是否调用过 where 区分
 * listAllKeys（无 where，返回 ledgerKeys）与 listKeysOlderThan（有 where，返回 staleKeys）
 */
function buildCleanupService(
  overrides: {
    usedKeys?: string[];
    wordcloudUrl?: string | null;
    ledgerKeys?: string[];
    staleKeys?: string[];
    ossObjects?: Array<{ name: string; lastModified?: number }>;
    springFails?: boolean;
    wordcloudFails?: boolean;
  } = {},
) {
  const usedUrls: string[] = (overrides.usedKeys ?? []).map(
    (key) => PREFIX + key,
  );
  const springClient = {
    listOssReferenceUrls: overrides.springFails
      ? jest.fn().mockRejectedValue(new Error("spring down"))
      : jest.fn().mockResolvedValue({ data: usedUrls }),
  };
  const nacos = {
    call: overrides.wordcloudFails
      ? jest.fn().mockRejectedValue(new Error("fastapi down"))
      : jest.fn().mockResolvedValue({ data: overrides.wordcloudUrl ?? null }),
  };
  const oss = {
    extractKey: jest.fn((url: string) =>
      url.startsWith(PREFIX) ? url.slice(PREFIX.length) : null,
    ),
    getFileUrl: jest.fn((key: string) => PREFIX + key),
    isAllowedCleanupKey: jest.fn((key: string) =>
      ["pic/", "pdf/", "excel/", "articles/"].some((p) => key.startsWith(p)),
    ),
    listObjects: jest.fn().mockResolvedValue(overrides.ossObjects ?? []),
    deleteObjects: jest.fn().mockResolvedValue(1),
  };
  const repository = {
    createQueryBuilder: jest.fn(() => {
      const qb: any = {
        insert: jest.fn(() => {
          qb._isInsert = true;
          return qb;
        }),
        into: jest.fn(() => qb),
        values: jest.fn((values: unknown) => {
          // 补录条数由 insert 的行数决定，据此生成等量的 generatedMaps
          qb._insertCount = Array.isArray(values) ? values.length : 1;
          return qb;
        }),
        orIgnore: jest.fn(() => qb),
        select: jest.fn(() => qb),
        where: jest.fn(() => {
          qb._hasWhere = true;
          return qb;
        }),
        andWhere: jest.fn(() => qb),
        update: jest.fn(() => qb),
        set: jest.fn(() => qb),
        execute: jest.fn().mockImplementation(async () => ({
          generatedMaps: qb._isInsert
            ? Array.from({ length: qb._insertCount ?? 0 }, (_, i) => ({
                id: i,
              }))
            : [],
        })),
        getRawMany: jest.fn().mockImplementation(async () => {
          const keys = qb._hasWhere
            ? (overrides.staleKeys ?? [])
            : (overrides.ledgerKeys ?? []);
          return keys.map((key) => ({ oss_key: key }));
        }),
      };
      return qb;
    }),
    delete: jest.fn().mockResolvedValue({ affected: 1 }),
  };
  const logger = {
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
  };
  const service = new OssObjectService(
    repository as never,
    oss as never,
    nacos as never,
    springClient as never,
    logger as never,
  );
  return { service, oss, repository, springClient, nacos };
}

describe("OssObjectService 清理", () => {
  // 在用的历史对象不在账本时补录，且不进入删除
  it("补录在用历史对象且不删除", async () => {
    const { service, repository, oss } = buildCleanupService({
      usedKeys: ["pic/avatar.png"],
      ledgerKeys: [],
    });

    const result = await service.cleanup(false);

    expect(result.backfilled).toBeGreaterThan(0);
    expect(oss.deleteObjects).not.toHaveBeenCalled();
    expect(repository.createQueryBuilder).toHaveBeenCalled();
  });

  // 词云 URL 作为在用引用被纳入，避免被当成孤儿删除
  it("当前词云 URL 纳入在用引用", async () => {
    const { service, oss } = buildCleanupService({
      usedKeys: [],
      wordcloudUrl: PREFIX + "pic/wordcloud.png",
    });

    await service.cleanup(false);

    expect(oss.extractKey).toHaveBeenCalledWith(PREFIX + "pic/wordcloud.png");
    expect(oss.deleteObjects).not.toHaveBeenCalled();
  });

  // 超宽限期且无引用的账本对象被删除，同时删除账本记录
  it("删除超宽限期无引用对象并清理账本", async () => {
    const { service, oss, repository } = buildCleanupService({
      usedKeys: [],
      ledgerKeys: ["pic/stale.png"],
      staleKeys: ["pic/stale.png"],
    });

    await service.cleanup(false);

    expect(oss.deleteObjects).toHaveBeenCalledWith(["pic/stale.png"]);
    expect(repository.delete).toHaveBeenCalledWith([
      { oss_key: "pic/stale.png" },
    ]);
  });

  // OSS 孤儿对象（不在账本）超过宽限期后被删除
  it("删除 OSS 中不在账本的孤儿对象", async () => {
    const { service, oss } = buildCleanupService({
      usedKeys: [],
      ledgerKeys: [],
      ossObjects: [
        { name: "pdf/orphan.pdf", lastModified: Date.now() - 2 * 3600 * 1000 },
      ],
    });

    await service.cleanup(false);

    expect(oss.deleteObjects).toHaveBeenCalledWith(["pdf/orphan.pdf"]);
  });

  // 未满宽限期的孤儿对象不清理，避免刚导出的下载产物被删
  it("孤儿对象未超过宽限期时不删除", async () => {
    const { service, oss } = buildCleanupService({
      usedKeys: [],
      ledgerKeys: [],
      ossObjects: [
        {
          name: "articles/article-1.docx",
          lastModified: Date.now() - 60 * 1000,
        },
      ],
    });

    await service.cleanup(false);

    expect(oss.deleteObjects).not.toHaveBeenCalled();
  });

  // 非白名单前缀对象被跳过
  it("跳过非白名单前缀的 OSS 对象", async () => {
    const { service, oss } = buildCleanupService({
      ossObjects: [{ name: "config/settings.json" }],
    });

    await service.cleanup(false);

    expect(oss.deleteObjects).not.toHaveBeenCalled();
  });

  // dry-run 下不执行任何删除
  it("dry-run 下不删除 OSS 对象", async () => {
    const { service, oss } = buildCleanupService({
      staleKeys: ["pic/stale.png"],
      ossObjects: [{ name: "pdf/orphan.pdf" }],
    });

    const result = await service.cleanup(true);

    expect(oss.deleteObjects).not.toHaveBeenCalled();
    expect(result.deleted).toBeGreaterThan(0);
  });

  // 引用来源查询失败时跳过删除，避免误删
  it("引用来源查询失败时跳过删除", async () => {
    const { service, oss } = buildCleanupService({
      springFails: true,
      staleKeys: ["pic/stale.png"],
      ossObjects: [{ name: "pdf/orphan.pdf" }],
    });

    await service.cleanup(false);

    expect(oss.deleteObjects).not.toHaveBeenCalled();
  });

  // 词云来源查询失败时同样跳过删除（fail-closed 覆盖两个来源）
  it("词云来源查询失败时跳过删除", async () => {
    const { service, oss } = buildCleanupService({
      wordcloudFails: true,
      ossObjects: [{ name: "pdf/orphan.pdf" }],
    });

    await service.cleanup(false);

    expect(oss.deleteObjects).not.toHaveBeenCalled();
  });
});
