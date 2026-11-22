import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import {
  IsEnum,
  IsNotEmpty,
  IsNumber,
  IsNumberString,
  IsOptional,
  IsString,
} from "class-validator";
import { Messages } from "src/common/constants";
import { ExposeName } from "src/common/utils/snakeCase";

export enum ArticleAction {
  ADD = "add",
  SEARCH = "search",
  EDIT = "edit",
  DELETE = "delete",
  PUBLISH = "publish",
  VIEW = "view",
  LIKE = "like",
  UNLIKE = "unlike",
  COLLECT = "collect",
  UNCOLLECT = "uncollect",
  FOCUS = "focus",
  UNFOCUS = "unfocus",
}

// RabbitMQ 消息接口定义
export interface ArticleLogMessage {
  action: ArticleAction;
  content: string | Record<string, unknown>;
  msg?: string;
  userId: number;
  articleId: number;
}

/**
 * 创建文章日志的请求DTO，包含用户ID、文章ID、操作类型与任意结构的操作内容
 */
export class CreateArticleLogDto {
  @ApiProperty({ description: "用户ID", example: "1" })
  @ExposeName()
  @IsNumber({}, { message: Messages.DTO_USER_ID_MUST_BE_NUMBER })
  @IsNotEmpty({ message: Messages.DTO_USER_ID_NOT_EMPTY })
  userId!: number;

  @ApiProperty({ description: "文章ID", example: "1" })
  @ExposeName()
  @IsNumber({}, { message: Messages.DTO_ARTICLE_ID_MUST_BE_NUMBER })
  @IsNotEmpty({ message: Messages.DTO_ARTICLE_ID_NOT_EMPTY })
  articleId!: number;

  @ApiProperty({
    description: "操作类型",
    enum: ArticleAction,
    example: ArticleAction.EDIT,
  })
  @IsEnum(ArticleAction, { message: Messages.DTO_ACTION_INVALID_ENUM })
  action!: ArticleAction;

  @ApiProperty({
    description: "任意结构的操作内容（JSON）",
    type: Object,
    example: { field: "title", oldValue: "旧标题", newValue: "新标题" },
  })
  content!: Record<string, unknown>;

  @ApiPropertyOptional({ description: "操作说明", example: "修改了文章标题" })
  @IsOptional()
  @IsString({ message: Messages.DTO_ACTION_MESSAGE_MUST_BE_STRING })
  msg?: string;
}

/**
 * 文章日志分页查询条件DTO，支持用户、文章、操作类型与时间范围过滤及分页参数
 */
export class QueryArticleLogDto {
  @ApiPropertyOptional({ description: "用户ID" })
  @ExposeName()
  @IsOptional()
  @IsNumberString({}, { message: Messages.DTO_USER_ID_MUST_BE_NUMBER_STRING })
  userId?: string;

  @ApiPropertyOptional({ description: "文章ID" })
  @ExposeName()
  @IsOptional()
  @IsNumberString(
    {},
    { message: Messages.DTO_ARTICLE_ID_MUST_BE_NUMBER_STRING },
  )
  articleId?: string;

  @ApiPropertyOptional({ description: "用户名（模糊搜索）" })
  @IsOptional()
  @IsString({ message: Messages.DTO_USERNAME_MUST_BE_STRING })
  username?: string;

  @ApiPropertyOptional({ description: "文章标题（模糊搜索）" })
  @ExposeName()
  @IsOptional()
  @IsString({ message: Messages.DTO_ARTICLE_TITLE_MUST_BE_STRING })
  articleTitle?: string;

  @ApiPropertyOptional({
    description: "操作类型",
    enum: [
      ArticleAction.ADD,
      ArticleAction.SEARCH,
      ArticleAction.EDIT,
      ArticleAction.DELETE,
      ArticleAction.PUBLISH,
      ArticleAction.VIEW,
      ArticleAction.LIKE,
      ArticleAction.UNLIKE,
      ArticleAction.COLLECT,
      ArticleAction.UNCOLLECT,
      ArticleAction.FOCUS,
      ArticleAction.UNFOCUS,
    ],
  })
  @IsOptional()
  @IsEnum(ArticleAction, { message: Messages.DTO_ACTION_INVALID_ENUM })
  action?: ArticleAction;

  @ApiPropertyOptional({ description: "开始时间（格式：yyyy-MM-dd HH:mm:ss）" })
  @ExposeName()
  @IsOptional()
  @IsString({ message: Messages.DTO_START_TIME_MUST_BE_STRING })
  startTime?: string;

  @ApiPropertyOptional({ description: "结束时间（格式：yyyy-MM-dd HH:mm:ss）" })
  @ExposeName()
  @IsOptional()
  @IsString({ message: Messages.DTO_END_TIME_MUST_BE_STRING })
  endTime?: string;

  @ApiPropertyOptional({ description: "页码", example: "1" })
  @IsOptional()
  @IsNumberString({}, { message: Messages.DTO_PAGE_MUST_BE_NUMBER_STRING })
  page?: string;

  @ApiPropertyOptional({ description: "每页条数", example: "10" })
  @IsOptional()
  @IsNumberString({}, { message: Messages.DTO_PAGE_SIZE_MUST_BE_NUMBER_STRING })
  size?: string;

  @ApiPropertyOptional({
    description:
      "翻页游标，传上一页返回的 nextCursor 时忽略 page 并按 createdAt + _id 顺序取下一页",
  })
  @IsOptional()
  @IsString({ message: Messages.DTO_CURSOR_MUST_BE_STRING })
  cursor?: string;
}
