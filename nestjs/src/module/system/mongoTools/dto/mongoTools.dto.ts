import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import { Type } from "class-transformer";
import {
  ArrayMaxSize,
  ArrayMinSize,
  IsArray,
  IsInt,
  IsNotEmpty,
  IsObject,
  IsOptional,
  IsString,
  Max,
  Min,
} from "class-validator";
import { Messages, MongoTools } from "src/common/constants";
import { ExposeName } from "src/common/utils";

/**
 * MongoDB 查询 DTO
 *
 * 校验消息统一引用 Messages 常量，动态上限由函数型成员拼接
 */
export class QueryMongoDto {
  @ApiProperty({
    description: "集合名称（仅限白名单内的日志集合）",
    example: "articlelogs",
  })
  @ExposeName()
  @IsString({ message: Messages.DTO_COLLECTION_NAME_MUST_BE_STRING })
  @IsNotEmpty({ message: Messages.DTO_COLLECTION_NAME_NOT_EMPTY })
  collectionName!: string;

  @ApiPropertyOptional({
    description: "查询过滤条件（MongoDB 查询对象）",
    example: { action: "view" },
  })
  @IsOptional()
  @IsObject({ message: Messages.DTO_FILTER_MUST_BE_OBJECT })
  filter?: Record<string, unknown>;

  @ApiPropertyOptional({
    description: "返回条数上限",
    example: 10,
    default: 10,
  })
  @Type(() => Number)
  @IsOptional()
  @IsInt({ message: Messages.DTO_LIMIT_MUST_BE_INT })
  @Min(1, { message: Messages.DTO_LIMIT_MIN_ONE })
  @Max(50, { message: Messages.DTO_LIMIT_MAX_FIFTY })
  limit?: number;
}

/**
 * MongoDB 聚合查询 DTO
 *
 * 说明：只读聚合管道，阶段合法性由服务层的白名单校验兜底，
 * 这里约束管道的基本形态与返回条数
 */
export class AggregateMongoDto {
  @ApiProperty({
    description: "集合名称（仅限白名单内的日志集合）",
    example: "apilogs",
  })
  @ExposeName()
  @IsString({ message: Messages.DTO_COLLECTION_NAME_MUST_BE_STRING })
  @IsNotEmpty({ message: Messages.DTO_COLLECTION_NAME_NOT_EMPTY })
  collectionName!: string;

  @ApiProperty({
    description:
      "聚合管道，每项为只包含一个操作符的对象，允许 $match/$project/$addFields/$group/$sort/$limit/$count/$unwind",
    example: [
      { $match: { response_time: { $gt: 200 } } },
      { $group: { _id: "$path", count: { $sum: 1 } } },
      { $sort: { count: -1 } },
    ],
  })
  // pipeline 是「对象数组」，必须显式声明元素类型：
  // 全局 ValidationPipe 开启了 enableImplicitConversion，装饰器又让 design:type 成为 Array，
  // 不声明 @Type 时 class-transformer 会把每个阶段对象转成空数组，阶段内容全部丢失
  @Type(() => Object)
  @IsArray({ message: Messages.DTO_PIPELINE_MUST_BE_ARRAY })
  @ArrayMinSize(1, { message: Messages.DTO_PIPELINE_MIN_ONE_STAGE })
  @ArrayMaxSize(MongoTools.MAX_PIPELINE_STAGES, {
    message: Messages.MONGO_PIPELINE_STAGES_EXCEEDED(
      MongoTools.MAX_PIPELINE_STAGES,
    ),
  })
  pipeline!: Record<string, unknown>[];

  @ApiPropertyOptional({
    description: "聚合结果返回条数上限",
    example: 20,
    default: 20,
  })
  @Type(() => Number)
  @IsOptional()
  @IsInt({ message: Messages.DTO_LIMIT_MUST_BE_INT })
  @Min(1, { message: Messages.DTO_LIMIT_MIN_ONE })
  @Max(MongoTools.MAX_AGGREGATE_DOCS, {
    message: Messages.MONGO_RESULT_LIMIT_EXCEEDED(
      MongoTools.MAX_AGGREGATE_DOCS,
    ),
  })
  limit?: number;
}
