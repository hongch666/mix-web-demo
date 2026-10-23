import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import {
  ArticleAction,
  CreateArticleLogDto,
  QueryArticleLogDto,
} from "./articleLog.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

// 构造合法的文章日志消息体，测试中按需覆盖字段，带 @ExposeName 的字段请求键名为 snake_case
const validCreatePayload = () => ({
  user_id: 1,
  article_id: 2,
  action: ArticleAction.EDIT,
  content: { field: "title", oldValue: "旧标题", newValue: "新标题" },
});

describe("CreateArticleLogDto", () => {
  // 验证合法日志消息体通过校验
  it("验证合法日志消息体通过校验", async () => {
    const dto = (await pipe.transform(validCreatePayload(), {
      type: "body" as const,
      metatype: CreateArticleLogDto,
    })) as CreateArticleLogDto;

    expect(dto.userId).toBe(1);
    expect(dto.articleId).toBe(2);
    expect(dto.action).toBe(ArticleAction.EDIT);
    expect(dto.content).toEqual({
      field: "title",
      oldValue: "旧标题",
      newValue: "新标题",
    });
  });

  // 验证可选的操作说明缺省时放行
  it("验证可选操作说明缺省通过校验", async () => {
    const dto = (await pipe.transform(validCreatePayload(), {
      type: "body" as const,
      metatype: CreateArticleLogDto,
    })) as CreateArticleLogDto;

    expect(dto.msg).toBeUndefined();
  });

  // 验证必填字段缺失被拒绝
  it("验证缺失用户ID与文章ID被拒绝", async () => {
    await expect(
      pipe.transform(
        { ...validCreatePayload(), user_id: undefined },
        { type: "body" as const, metatype: CreateArticleLogDto },
      ),
    ).rejects.toThrow();

    await expect(
      pipe.transform(
        { ...validCreatePayload(), article_id: undefined },
        { type: "body" as const, metatype: CreateArticleLogDto },
      ),
    ).rejects.toThrow();
  });

  // 验证操作类型超出枚举范围被拒绝
  it("验证非法操作类型被拒绝", async () => {
    await expect(
      pipe.transform(
        { ...validCreatePayload(), action: "download" },
        { type: "body" as const, metatype: CreateArticleLogDto },
      ),
    ).rejects.toThrow();
  });
});

describe("QueryArticleLogDto", () => {
  // 验证合法查询参数通过校验
  it("验证合法查询参数通过校验", async () => {
    const dto = (await pipe.transform(
      {
        user_id: "1",
        article_id: "2",
        action: ArticleAction.VIEW,
        page: "1",
        size: "10",
      },
      { type: "query" as const, metatype: QueryArticleLogDto },
    )) as QueryArticleLogDto;

    expect(dto.userId).toBe("1");
    expect(dto.articleId).toBe("2");
    expect(dto.action).toBe(ArticleAction.VIEW);
    expect(dto.page).toBe("1");
  });

  // 验证全部字段可选，空查询对象放行
  it("验证空查询对象通过校验", async () => {
    const dto = (await pipe.transform(
      {},
      { type: "query" as const, metatype: QueryArticleLogDto },
    )) as QueryArticleLogDto;

    expect(dto.action).toBeUndefined();
  });

  // 验证操作类型超出枚举范围被拒绝
  it("验证非法查询操作类型被拒绝", async () => {
    await expect(
      pipe.transform(
        { action: "download" },
        { type: "query" as const, metatype: QueryArticleLogDto },
      ),
    ).rejects.toThrow();
  });

  // 验证分页参数不是数字字符串被拒绝
  it("验证非数字字符串每页条数被拒绝", async () => {
    await expect(
      pipe.transform(
        { size: "ten" },
        { type: "query" as const, metatype: QueryArticleLogDto },
      ),
    ).rejects.toThrow();
  });
});
