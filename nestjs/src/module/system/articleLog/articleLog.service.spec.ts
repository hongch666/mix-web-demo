import { ArticleLogService } from "./articleLog.service";

/**
 * 构造浏览分布用例所需的服务实例，索引初始化与远程调用全部替换为替身
 * @param aggregated 聚合返回的浏览记录
 * @param articles Spring 批量查询返回的文章
 */
function createService(
  aggregated: Array<{ _id: number; views: number }>,
  articles: Array<{ id: number; title: string }>,
): { service: ArticleLogService; aggregate: jest.Mock } {
  const aggregate = jest.fn().mockReturnValue({
    exec: jest.fn().mockResolvedValue(aggregated),
  });
  const logModel = {
    collection: {
      getIndexes: jest.fn().mockResolvedValue([]),
      createIndex: jest.fn().mockResolvedValue("created"),
    },
    aggregate,
  };
  const springClient = {
    getArticleByIds: jest.fn().mockResolvedValue({ data: articles }),
  };
  const logger = { info: jest.fn(), error: jest.fn(), warning: jest.fn() };
  const service = new ArticleLogService(
    logModel as never,
    springClient as never,
    logger as never,
  );
  return { service, aggregate };
}

describe("ArticleLogService.getViewDistribution", () => {
  // 验证文章已删除（查不到标题）的浏览记录被丢弃，总浏览量与列表口径一致
  it("验证未知文章的浏览记录被丢弃", async () => {
    const { service } = createService(
      [
        { _id: 115, views: 18 },
        { _id: 8947, views: 12 },
      ],
      [{ id: 8947, title: "编程入门" }],
    );

    const result = await service.getViewDistribution(1);

    expect(result).toEqual({
      total_views: 12,
      articles: [{ article_id: 8947, title: "编程入门", views: 12 }],
    });
  });

  // 验证全部文章都查不到时返回空分布，不再产生未知文章占位
  it("验证文章全部缺失时返回空分布", async () => {
    const { service } = createService([{ _id: 115, views: 18 }], []);

    const result = await service.getViewDistribution(1);

    expect(result).toEqual({ total_views: 0, articles: [] });
  });
});
