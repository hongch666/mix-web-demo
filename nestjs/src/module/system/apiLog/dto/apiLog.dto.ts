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

export enum ApiMethod {
  GET = "GET",
  POST = "POST",
  PUT = "PUT",
  DELETE = "DELETE",
  PATCH = "PATCH",
  OPTIONS = "OPTIONS",
  HEAD = "HEAD",
}

// RabbitMQ 消息接口定义
export interface ApiLogMessage {
  userId: number;
  username: string;
  apiDescription: string;
  apiPath: string;
  apiMethod: ApiMethod;
  queryParams?: Record<string, unknown>;
  pathParams?: Record<string, unknown>;
  requestBody?: Record<string, unknown> | string | null;
  responseTime: number;
}

/**
 * 创建 API 日志的请求DTO，包含用户、接口描述、路径、方法与响应时间等字段
 */
export class CreateApiLogDto {
  @ApiProperty({ description: "用户ID", example: 1 })
  @ExposeName()
  @IsNumber({}, { message: Messages.DTO_USER_ID_MUST_BE_NUMBER })
  @IsNotEmpty({ message: Messages.DTO_USER_ID_NOT_EMPTY })
  userId!: number;

  @ApiProperty({ description: "用户名", example: "admin" })
  @IsString({ message: Messages.DTO_USERNAME_MUST_BE_STRING })
  @IsNotEmpty({ message: Messages.DTO_USERNAME_NOT_EMPTY })
  username!: string;

  @ApiProperty({ description: "API描述", example: "获取用户信息" })
  @ExposeName()
  @IsString({ message: Messages.DTO_API_DESCRIPTION_MUST_BE_STRING })
  @IsNotEmpty({ message: Messages.DTO_API_DESCRIPTION_NOT_EMPTY })
  apiDescription!: string;

  @ApiProperty({ description: "API路径", example: "/api/users/1" })
  @ExposeName()
  @IsString({ message: Messages.DTO_API_PATH_MUST_BE_STRING })
  @IsNotEmpty({ message: Messages.DTO_API_PATH_NOT_EMPTY })
  apiPath!: string;

  @ApiProperty({
    description: "API方法",
    enum: Object.values(ApiMethod),
    example: ApiMethod.GET,
  })
  @ExposeName()
  @IsEnum(ApiMethod, { message: Messages.DTO_API_METHOD_INVALID_ENUM })
  @IsNotEmpty({ message: Messages.DTO_API_METHOD_NOT_EMPTY })
  apiMethod!: ApiMethod;

  @ApiPropertyOptional({
    description: "查询参数",
    example: { page: 1, size: 10 },
  })
  @ExposeName()
  @IsOptional()
  queryParams?: Record<string, unknown>;

  @ApiPropertyOptional({ description: "路径参数", example: { id: "1" } })
  @ExposeName()
  @IsOptional()
  pathParams?: Record<string, unknown>;

  @ApiPropertyOptional({ description: "请求体", example: { name: "test" } })
  @ExposeName()
  @IsOptional()
  requestBody?: Record<string, unknown>;

  @ApiProperty({ description: "响应时间（毫秒）", example: 100 })
  @ExposeName()
  @IsNumber({}, { message: Messages.DTO_RESPONSE_TIME_MUST_BE_NUMBER })
  @IsNotEmpty({ message: Messages.DTO_RESPONSE_TIME_NOT_EMPTY })
  responseTime!: number;
}

/**
 * API 日志分页查询条件DTO，支持用户、路径、方法与时间范围过滤及分页参数
 */
export class QueryApiLogDto {
  @ApiPropertyOptional({ description: "用户ID" })
  @ExposeName()
  @IsOptional()
  @IsNumberString({}, { message: Messages.DTO_USER_ID_MUST_BE_NUMBER_STRING })
  userId?: string;

  @ApiPropertyOptional({ description: "用户名（模糊搜索）" })
  @IsOptional()
  @IsString({ message: Messages.DTO_USERNAME_MUST_BE_STRING })
  username?: string;

  @ApiPropertyOptional({ description: "API描述（模糊搜索）" })
  @ExposeName()
  @IsOptional()
  @IsString({ message: Messages.DTO_API_DESCRIPTION_MUST_BE_STRING })
  apiDescription?: string;

  @ApiPropertyOptional({ description: "API路径（模糊搜索）" })
  @ExposeName()
  @IsOptional()
  @IsString({ message: Messages.DTO_API_PATH_MUST_BE_STRING })
  apiPath?: string;

  @ApiPropertyOptional({
    description: "API方法",
    enum: Object.values(ApiMethod),
  })
  @ExposeName()
  @IsOptional()
  @IsEnum(ApiMethod, { message: Messages.DTO_API_METHOD_INVALID_ENUM })
  apiMethod?: ApiMethod;

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
