import { ApiProperty, ApiPropertyOptional } from "@nestjs/swagger";
import { IsNotEmpty, IsObject, IsOptional, IsString } from "class-validator";
import { Messages } from "src/common/constants";

export class SqlQueryDto {
  @ApiProperty({
    description: "参数化SQL（使用 :paramName 占位符）",
    example:
      "SELECT * FROM user_table_settings WHERE user_id = :userId LIMIT :limit",
  })
  @IsString({ message: Messages.SQL_PROXY_QUERY_MUST_BE_STRING })
  @IsNotEmpty({ message: Messages.SQL_PROXY_QUERY_NOT_EMPTY })
  query!: string;

  @ApiPropertyOptional({
    description: "参数键值对",
    example: { userId: 1, limit: 10 },
  })
  @IsOptional()
  @IsObject({ message: Messages.SQL_PROXY_PARAMS_MUST_BE_OBJECT })
  params?: Record<string, unknown>;
}
