import { applyDecorators } from "@nestjs/common";
import { ApiResponse as SwaggerApiResponse } from "@nestjs/swagger";
import type { SchemaObject } from "@nestjs/swagger/dist/interfaces/open-api-spec.interface";

export interface SwaggerResponseOptions {
  data?: SchemaObject;
  description?: string;
  status?: number;
}

function describeSchema(
  schema: SchemaObject,
  fieldName = "返回数据",
): SchemaObject {
  const properties = schema.properties as
    | Record<string, SchemaObject>
    | undefined;
  return {
    ...schema,
    description: schema.description ?? `${fieldName}`,
    ...(properties
      ? {
          properties: Object.fromEntries(
            Object.entries(properties).map(([name, property]) => [
              name,
              describeSchema(property, `${name}字段`),
            ]),
          ),
        }
      : {}),
    ...(schema.items &&
    typeof schema.items === "object" &&
    !Array.isArray(schema.items)
      ? { items: describeSchema(schema.items as SchemaObject, "列表项") }
      : {}),
  };
}

/** 为统一响应包装体声明可见的 data schema */
export function ApiResponseModel(
  options: SwaggerResponseOptions = {},
): MethodDecorator & ClassDecorator {
  const data: SchemaObject = options.data ?? { type: "object" };
  const responseSchema: SchemaObject = {
    type: "object",
    description: "统一接口响应体",
    properties: {
      code: {
        type: "integer",
        format: "int32",
        example: 200,
        description: "响应码，与 HTTP 状态码一致",
      },
      msg: { type: "string", example: "success", description: "响应消息" },
      data: describeSchema(data),
    },
    required: ["code", "msg", "data"],
  };

  return applyDecorators(
    SwaggerApiResponse({
      status: options.status ?? 200,
      description: options.description ?? "成功",
      schema: responseSchema,
    }),
  );
}

/** 声明通过 Location 响应头完成跳转的 HTTP 响应 */
export function ApiRedirectResponse(
  description = "重定向",
  status = 302,
): MethodDecorator & ClassDecorator {
  return applyDecorators(
    SwaggerApiResponse({
      status,
      description,
      headers: {
        Location: {
          description: "重定向地址",
          schema: { type: "string" },
        },
      },
    }),
  );
}

export const SwaggerNullData: SchemaObject = { type: "null" };
export const SwaggerStringData: SchemaObject = { type: "string" };
export const SwaggerObjectData: SchemaObject = { type: "object" };

export const SwaggerGithubAuthorizeData: SchemaObject = {
  type: "object",
  description: "GitHub OAuth 授权信息",
  properties: {
    authorizeUrl: { type: "string", description: "GitHub OAuth 授权地址" },
    state: { type: "string", description: "OAuth 防跨站请求伪造状态值" },
  },
};

export const SwaggerUploadResultData: SchemaObject = {
  type: "object",
  description: "上传文件结果",
  properties: {
    originalFilename: { type: "string", description: "原始文件名" },
    ossFilename: { type: "string", description: "OSS 文件名" },
    ossUrl: { type: "string", description: "OSS 文件访问地址" },
  },
  required: ["originalFilename", "ossFilename", "ossUrl"],
};

export const SwaggerArticleSearchHistoryData: SchemaObject = {
  type: "object",
  description: "用户最近搜索关键词",
  properties: {
    keywords: {
      type: "array",
      description: "去重后的搜索关键词列表",
      items: { type: "string", description: "搜索关键词" },
    },
  },
};

export const SwaggerSearchKeywordsData: SchemaObject = {
  type: "array",
  description: "所有去重后的搜索关键词",
  items: { type: "string", description: "搜索关键词" },
};

export const SwaggerTableSettingsListData: SchemaObject = {
  type: "array",
  description: "当前用户保存的表格列配置列表",
  items: {
    $ref: "#/components/schemas/TableSettings",
    description: "单条表格列配置",
  },
};

export const SwaggerTableSettingsData: SchemaObject = {
  description: "当前用户在指定页面保存的列配置",
  oneOf: [{ $ref: "#/components/schemas/TableSettings" }, { type: "null" }],
};

const stringField = (description: string): SchemaObject => ({
  type: "string",
  description,
});
const numberField = (description: string): SchemaObject => ({
  type: "number",
  description,
});

const articleLogItem: SchemaObject = {
  type: "object",
  description: "文章日志记录",
  properties: {
    _id: stringField("日志 ID"),
    userId: numberField("用户 ID"),
    username: stringField("用户名"),
    articleId: numberField("文章 ID"),
    articleTitle: stringField("文章标题"),
    action: stringField("操作类型"),
    content: { type: "object", description: "操作内容" },
    msg: stringField("操作说明"),
    createdAt: stringField("创建时间"),
    updatedAt: stringField("更新时间"),
  },
};

export const SwaggerArticleLogPageData: SchemaObject = {
  type: "object",
  description: "文章日志分页结果",
  properties: {
    total: numberField("日志总数"),
    list: { type: "array", description: "日志列表", items: articleLogItem },
  },
};

export const SwaggerArticleLogSyncData: SchemaObject = {
  type: "object",
  description: "文章日志增量同步结果",
  properties: {
    list: { type: "array", description: "日志列表", items: articleLogItem },
    nextCursor: stringField("下一页游标"),
  },
};

export const SwaggerArticleViewDistributionData: SchemaObject = {
  type: "object",
  description: "文章浏览次数分布",
  properties: {
    total_views: numberField("总浏览次数"),
    articles: {
      type: "array",
      description: "文章浏览统计列表",
      items: {
        type: "object",
        properties: {
          article_id: numberField("文章 ID"),
          title: stringField("文章标题"),
          views: numberField("浏览次数"),
        },
      },
    },
  },
};

const apiLogItem: SchemaObject = {
  type: "object",
  description: "API 日志记录",
  properties: {
    _id: stringField("日志 ID"),
    userId: numberField("用户 ID"),
    username: stringField("用户名"),
    apiDescription: stringField("接口描述"),
    apiPath: stringField("接口路径"),
    apiMethod: stringField("请求方法"),
    queryParams: { type: "object", description: "查询参数" },
    pathParams: { type: "object", description: "路径参数" },
    requestBody: { type: "object", description: "请求体" },
    responseTime: numberField("响应耗时（毫秒）"),
    createdAt: stringField("创建时间"),
    updatedAt: stringField("更新时间"),
  },
};

export const SwaggerApiLogPageData: SchemaObject = {
  type: "object",
  description: "API 日志分页结果",
  properties: {
    total: numberField("日志总数"),
    list: { type: "array", description: "日志列表", items: apiLogItem },
  },
};

export const SwaggerApiLogSyncData: SchemaObject = {
  type: "object",
  description: "API 日志增量同步结果",
  properties: {
    list: { type: "array", description: "日志列表", items: apiLogItem },
    nextCursor: stringField("下一页游标"),
  },
};

export const SwaggerApiLogAverageData: SchemaObject = {
  type: "array",
  description: "接口平均响应时间统计",
  items: {
    type: "object",
    properties: {
      api_path: stringField("接口路径"),
      api_method: stringField("请求方法"),
      api_description: stringField("接口描述"),
      avg_response_time: numberField("平均响应时间（毫秒）"),
      count: numberField("调用次数"),
    },
  },
};

export const SwaggerApiLogCalledCountData: SchemaObject = {
  type: "array",
  description: "接口调用次数统计",
  items: {
    type: "object",
    properties: {
      api_path: stringField("接口路径"),
      api_method: stringField("请求方法"),
      api_description: stringField("接口描述"),
      call_count: numberField("调用次数"),
      avg_response_time: numberField("平均响应时间（毫秒）"),
    },
  },
};

export const SwaggerSqlTablesData: SchemaObject = {
  type: "array",
  description: "数据表结构列表",
  items: {
    type: "object",
    properties: {
      table: stringField("表名"),
      rowCount: numberField("数据行数"),
      columns: {
        type: "array",
        description: "列定义",
        items: { type: "object" },
      },
    },
  },
};

export const SwaggerSqlQueryData: SchemaObject = {
  type: "object",
  description: "SQL 查询结果",
  properties: {
    columns: { type: "array", description: "列名", items: stringField("列名") },
    rows: { type: "array", description: "行数据", items: { type: "array" } },
    rowCount: numberField("行数"),
  },
};

export const SwaggerMongoCollectionsData: SchemaObject = {
  type: "array",
  description: "MongoDB 集合信息列表",
  items: {
    type: "object",
    properties: {
      name: stringField("集合名称"),
      document_count: numberField("文档数量"),
      sample_fields: {
        type: "array",
        description: "示例字段名",
        items: stringField("字段名"),
      },
    },
  },
};

export const SwaggerMongoQueryData: SchemaObject = {
  type: "array",
  description: "MongoDB 查询结果",
  items: { type: "object", description: "MongoDB 文档" },
};
