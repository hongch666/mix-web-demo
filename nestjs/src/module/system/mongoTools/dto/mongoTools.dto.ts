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
import { MongoTools } from "src/common/constants";
import { ExposeName } from "src/framework/serializer/snakeCase.serializer";

/**
 * MongoDB 查询 DTO
 *
 * 说明：class-validator 注解内的校验消息使用内联字符串，
 * 保证注解与消息就地可读，不走常量类
 */
export class QueryMongoDto {
  @ApiProperty({
    description: "集合名称（仅限白名单内的日志集合）",
    example: "articlelogs",
  })
  @ExposeName()
  @IsString({ message: "集合名称必须是字符串" })
  @IsNotEmpty({ message: "集合名称不能为空" })
  collectionName!: string;

  @ApiPropertyOptional({
    description: "查询过滤条件（MongoDB 查询对象）",
    example: { action: "view" },
  })
  @IsOptional()
  @IsObject({ message: "过滤条件必须是对象" })
  filter?: Record<string, unknown>;

  @ApiPropertyOptional({
    description: "返回条数上限",
    example: 10,
    default: 10,
  })
  @Type(() => Number)
  @IsOptional()
  @IsInt({ message: "返回条数必须是整数" })
  @Min(1, { message: "返回条数最小为1" })
  @Max(50, { message: "返回条数最大为50" })
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
  @IsString({ message: "集合名称必须是字符串" })
  @IsNotEmpty({ message: "集合名称不能为空" })
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
  @IsArray({ message: "聚合管道必须是数组" })
  @ArrayMinSize(1, { message: "聚合管道至少需要一个阶段" })
  @ArrayMaxSize(MongoTools.MAX_PIPELINE_STAGES, {
    message: `聚合管道阶段数不能超过 ${MongoTools.MAX_PIPELINE_STAGES}`,
  })
  pipeline!: Record<string, unknown>[];

  @ApiPropertyOptional({
    description: "聚合结果返回条数上限",
    example: 20,
    default: 20,
  })
  @Type(() => Number)
  @IsOptional()
  @IsInt({ message: "返回条数必须是整数" })
  @Min(1, { message: "返回条数最小为1" })
  @Max(MongoTools.MAX_AGGREGATE_DOCS, {
    message: `返回条数最大为${MongoTools.MAX_AGGREGATE_DOCS}`,
  })
  limit?: number;
}
