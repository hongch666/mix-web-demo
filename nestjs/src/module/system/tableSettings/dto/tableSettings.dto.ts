import { ApiProperty } from "@nestjs/swagger";
import { Type } from "class-transformer";
import {
  IsArray,
  IsInt,
  IsNotEmpty,
  IsOptional,
  Length,
  Matches,
  Min,
  ValidateNested,
} from "class-validator";

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

/**
 * 列设置接口的用户范围查询参数
 * 缺省时操作当前登录用户的数据，指定他人时要求当前用户为管理员
 */
export class TableSettingsQueryDto {
  @ApiProperty({
    description: "目标用户ID，缺省为当前登录用户",
    example: 1,
    required: false,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt({ message: "目标用户ID必须是整数" })
  @Min(1, { message: "目标用户ID必须大于0" })
  user_id?: number;
}

/**
 * 列设置接口的页面标识路径参数
 * 页面标识会参与两级缓存 key 拼接，因此限制长度与字符集，避免产生无界或异常的缓存键
 */
export class TableKeyParamDto {
  @ApiProperty({ description: "页面标识", example: "articles" })
  @Length(1, 64, { message: "页面标识长度必须在1到64之间" })
  @Matches(/^[A-Za-z0-9_-]+$/, {
    message: "页面标识只能包含字母、数字、下划线与中划线",
  })
  table_key!: string;
}
