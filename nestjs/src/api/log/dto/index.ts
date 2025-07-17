import {
  IsEnum,
  IsNotEmpty,
  IsNumber,
  IsNumberString,
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

export class QueryArticleLogDto {
  @ApiPropertyOptional({ description: '用户ID' })
  @IsOptional()
  @IsNumberString()
  userId?: string;

  @ApiPropertyOptional({ description: '文章ID' })
  @IsOptional()
  @IsNumberString()
  articleId?: string;

  @ApiPropertyOptional({ description: '用户名（模糊搜索）' })
  @IsOptional()
  @IsString()
  username?: string;

  @ApiPropertyOptional({ description: '文章标题（模糊搜索）' })
  @IsOptional()
  @IsString()
  articleTitle?: string;

  @ApiPropertyOptional({
    description: '操作类型',
    enum: ['add', 'search', 'edit', 'delete'],
  })
  @IsOptional()
  @IsEnum(['add', 'search', 'edit', 'delete'])
  action?: string;

  @ApiPropertyOptional({ description: '开始时间（格式：yyyy-MM-dd HH:mm:ss）' })
  @IsOptional()
  @IsString()
  startTime?: string;

  @ApiPropertyOptional({ description: '结束时间（格式：yyyy-MM-dd HH:mm:ss）' })
  @IsOptional()
  @IsString()
  endTime?: string;

  @ApiPropertyOptional({ description: '页码', example: '1' })
  @IsOptional()
  @IsNumberString()
  page?: string;

  @ApiPropertyOptional({ description: '每页条数', example: '10' })
  @IsOptional()
  @IsNumberString()
  size?: string;
}
