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

import { Messages } from "src/common/constants/messages.constants";

export class QueryMongoDto {
  @ApiProperty({
    description: "集合名称（仅限白名单内的日志集合）",
    example: "articlelogs",
  })
  @ExposeName()
  @IsString({ message: Messages.VALIDATION_COLLECTION_NAME_STRING })
  @IsNotEmpty({ message: Messages.VALIDATION_COLLECTION_NAME_NOT_EMPTY })
  collectionName!: string;

  @ApiPropertyOptional({
    description: "查询过滤条件（MongoDB 查询对象）",
    example: { action: "view" },
  })
  @IsOptional()
  @IsObject({ message: Messages.VALIDATION_FILTER_OBJECT })
  filter?: Record<string, unknown>;

  @ApiPropertyOptional({
    description: "返回条数上限",
    example: 10,
    default: 10,
  })
  @Type(() => Number)
  @IsOptional()
  @IsInt({ message: Messages.VALIDATION_LIMIT_INT })
  @Min(1, { message: Messages.VALIDATION_LIMIT_MIN })
  @Max(50, { message: Messages.VALIDATION_LIMIT_MAX })
  limit?: number;
}
