import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import {
  IsEnum,
  IsNotEmpty,
  IsNumber,
  IsNumberString,
  IsOptional,
  IsString,
} from "class-validator";

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
  content: string | Record<string, any>;
  msg?: string;
  user_id: number;
  article_id: number;
}

export class CreateArticleLogDto {
  @ApiProperty({ description: "用户ID", example: "1" })
  @IsNumber({}, { message: "用户ID必须是数字" })
  @IsNotEmpty({ message: "用户ID不能为空" })
  userId!: number;

  @ApiProperty({ description: "文章ID", example: "1" })
  @IsNumber({}, { message: "文章ID必须是数字" })
  @IsNotEmpty({ message: "文章ID不能为空" })
  articleId!: number;

  @ApiProperty({
    description: "操作类型",
    enum: ArticleAction,
    example: ArticleAction.EDIT,
  })
  @IsEnum(ArticleAction, { message: "操作类型必须是有效的枚举值" })
  action!: ArticleAction;

  @ApiProperty({
    description: "任意结构的操作内容（JSON）",
    type: Object,
    example: { field: "title", oldValue: "旧标题", newValue: "新标题" },
  })
  content!: Record<string, any>;

  @ApiPropertyOptional({ description: "操作说明", example: "修改了文章标题" })
  @IsOptional()
  @IsString({ message: "操作说明必须是字符串" })
  msg?: string;
}

export class QueryArticleLogDto {
  @ApiPropertyOptional({ description: "用户ID" })
  @IsOptional()
  @IsNumberString({}, { message: "用户ID必须是数字字符串" })
  userId?: string;

  @ApiPropertyOptional({ description: "文章ID" })
  @IsOptional()
  @IsNumberString({}, { message: "文章ID必须是数字字符串" })
  articleId?: string;

  @ApiPropertyOptional({ description: "用户名（模糊搜索）" })
  @IsOptional()
  @IsString({ message: "用户名必须是字符串" })
  username?: string;

  @ApiPropertyOptional({ description: "文章标题（模糊搜索）" })
  @IsOptional()
  @IsString({ message: "文章标题必须是字符串" })
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
  @IsEnum(ArticleAction, { message: "操作类型必须是有效的枚举值" })
  action?: ArticleAction;

  @ApiPropertyOptional({ description: "开始时间（格式：yyyy-MM-dd HH:mm:ss）" })
  @IsOptional()
  @IsString({ message: "开始时间必须是字符串" })
  startTime?: string;

  @ApiPropertyOptional({ description: "结束时间（格式：yyyy-MM-dd HH:mm:ss）" })
  @IsOptional()
  @IsString({ message: "结束时间必须是字符串" })
  endTime?: string;

  @ApiPropertyOptional({ description: "页码", example: "1" })
  @IsOptional()
  @IsNumberString({}, { message: "页码必须是数字字符串" })
  page?: string;

  @ApiPropertyOptional({ description: "每页条数", example: "10" })
  @IsOptional()
  @IsNumberString({}, { message: "每页条数必须是数字字符串" })
  size?: string;
}
