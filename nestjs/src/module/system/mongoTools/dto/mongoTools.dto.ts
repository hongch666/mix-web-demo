import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import { Type } from "class-transformer";
import {
  IsInt,
  IsNotEmpty,
  IsObject,
  IsOptional,
  IsString,
  Max,
  Min,
} from "class-validator";
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
