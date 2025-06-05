import {
  IsEnum,
  IsNotEmpty,
  IsNumber,
  IsOptional,
  IsString,
} from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateArticleLogDto {
  @ApiProperty({ description: '用户ID', example: '1' })
  @IsNumber()
  @IsNotEmpty()
  userId: number;

  @ApiProperty({ description: '文章ID', example: '1' })
  @IsNumber()
  @IsNotEmpty()
  articleId: number;

  @ApiProperty({
    description: '操作类型',
    enum: ['add', 'search', 'edit', 'delete'],
    example: 'edit',
  })
  @IsEnum(['add', 'search', 'edit', 'delete'])
  action: string;

  @ApiProperty({
    description: '任意结构的操作内容（JSON）',
    type: Object,
    example: { field: 'title', oldValue: '旧标题', newValue: '新标题' },
  })
  content: Record<string, any>;

  @ApiPropertyOptional({ description: '操作说明', example: '修改了文章标题' })
  @IsOptional()
  @IsString()
  msg?: string;
}
