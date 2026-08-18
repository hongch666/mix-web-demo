import { ApiProperty } from "@nestjs/swagger";
import { Type } from "class-transformer";
import { IsArray, IsNotEmpty, ValidateNested } from "class-validator";

/**
 * 单列配置项
 */
export class ColumnConfigDto {
  @ApiProperty({ description: "列标识", example: "title" })
  @IsNotEmpty({ message: "列标识不能为空" })
  key!: string;

  @ApiProperty({ description: "是否可见", example: true })
  visible!: boolean;

  @ApiProperty({ description: "排序序号", example: 0 })
  order!: number;

  @ApiProperty({ description: "列宽度（像素）", example: 200, required: false })
  width?: number;
}

/**
 * 保存列设置的请求体
 */
export class SaveTableSettingsDto {
  @ApiProperty({
    description: "列配置列表",
    type: [ColumnConfigDto],
    example: [
      { key: "title", visible: true, order: 0, width: 200 },
      { key: "author", visible: true, order: 1, width: 120 },
      { key: "category", visible: false, order: 2, width: 100 },
    ],
  })
  @IsArray({ message: "列配置必须是数组" })
  @ValidateNested({ each: true, message: "列配置项格式不正确" })
  @Type(() => ColumnConfigDto)
  columns!: ColumnConfigDto[];
}
