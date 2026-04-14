import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import {
  IsEnum,
  IsNotEmpty,
  IsNumber,
  IsNumberString,
  IsOptional,
  IsString,
} from "class-validator";

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
  user_id: number;
  username: string;
  api_description: string;
  api_path: string;
  api_method: ApiMethod;
  query_params?: Record<string, any>;
  path_params?: Record<string, any>;
  request_body?: Record<string, any>;
  response_time: number;
}

export class CreateApiLogDto {
  @ApiProperty({ description: "用户ID", example: 1 })
  @IsNumber({}, { message: "用户ID必须是数字" })
  @IsNotEmpty({ message: "用户ID不能为空" })
  userId!: number;

  @ApiProperty({ description: "用户名", example: "admin" })
  @IsString({ message: "用户名必须是字符串" })
  @IsNotEmpty({ message: "用户名不能为空" })
  username!: string;

  @ApiProperty({ description: "API描述", example: "获取用户信息" })
  @IsString({ message: "API描述必须是字符串" })
  @IsNotEmpty({ message: "API描述不能为空" })
  apiDescription!: string;

  @ApiProperty({ description: "API路径", example: "/api/users/1" })
  @IsString({ message: "API路径必须是字符串" })
  @IsNotEmpty({ message: "API路径不能为空" })
  apiPath!: string;

  @ApiProperty({
    description: "API方法",
    enum: Object.values(ApiMethod),
    example: ApiMethod.GET,
  })
  @IsEnum(ApiMethod, { message: "API方法必须是有效的枚举值" })
  @IsNotEmpty({ message: "API方法不能为空" })
  apiMethod!: ApiMethod;

  @ApiPropertyOptional({
    description: "查询参数",
    example: { page: 1, size: 10 },
  })
  @IsOptional()
  queryParams?: Record<string, any>;

  @ApiPropertyOptional({ description: "路径参数", example: { id: "1" } })
  @IsOptional()
  pathParams?: Record<string, any>;

  @ApiPropertyOptional({ description: "请求体", example: { name: "test" } })
  @IsOptional()
  requestBody?: Record<string, any>;

  @ApiProperty({ description: "响应时间（毫秒）", example: 100 })
  @IsNumber({}, { message: "响应时间必须是数字" })
  @IsNotEmpty({ message: "响应时间不能为空" })
  responseTime!: number;
}

export class QueryApiLogDto {
  @ApiPropertyOptional({ description: "用户ID" })
  @IsOptional()
  @IsNumberString({}, { message: "用户ID必须是数字字符串" })
  userId?: string;

  @ApiPropertyOptional({ description: "用户名（模糊搜索）" })
  @IsOptional()
  @IsString({ message: "用户名必须是字符串" })
  username?: string;

  @ApiPropertyOptional({ description: "API描述（模糊搜索）" })
  @IsOptional()
  @IsString({ message: "API描述必须是字符串" })
  apiDescription?: string;

  @ApiPropertyOptional({ description: "API路径（模糊搜索）" })
  @IsOptional()
  @IsString({ message: "API路径必须是字符串" })
  apiPath?: string;

  @ApiPropertyOptional({
    description: "API方法",
    enum: Object.values(ApiMethod),
  })
  @IsOptional()
  @IsEnum(ApiMethod, { message: "API方法必须是有效的枚举值" })
  apiMethod?: ApiMethod;

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
