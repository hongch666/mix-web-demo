import {
  IsNotEmpty,
  IsNumber,
  IsNumberString,
  IsOptional,
  IsString,
} from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CreateApiLogDto {
  @ApiProperty({ description: '用户ID', example: 1 })
  @IsNumber()
  @IsNotEmpty()
  userId: number;

  @ApiProperty({ description: '用户名', example: 'admin' })
  @IsString()
  @IsNotEmpty()
  username: string;

  @ApiProperty({ description: 'API描述', example: '获取用户信息' })
  @IsString()
  @IsNotEmpty()
  apiDescription: string;

  @ApiProperty({ description: 'API路径', example: '/api/users/1' })
  @IsString()
  @IsNotEmpty()
  apiPath: string;

  @ApiProperty({ description: 'API方法', example: 'GET' })
  @IsString()
  @IsNotEmpty()
  apiMethod: string;

  @ApiPropertyOptional({
    description: '查询参数',
    example: { page: 1, size: 10 },
  })
  @IsOptional()
  queryParams?: Record<string, any>;

  @ApiPropertyOptional({ description: '路径参数', example: { id: '1' } })
  @IsOptional()
  pathParams?: Record<string, any>;

  @ApiPropertyOptional({ description: '请求体', example: { name: 'test' } })
  @IsOptional()
  requestBody?: Record<string, any>;

  @ApiProperty({ description: '响应时间（毫秒）', example: 100 })
  @IsNumber()
  @IsNotEmpty()
  responseTime: number;
}

export class QueryApiLogDto {
  @ApiPropertyOptional({ description: '用户ID' })
  @IsOptional()
  @IsNumberString()
  userId?: string;

  @ApiPropertyOptional({ description: '用户名（模糊搜索）' })
  @IsOptional()
  @IsString()
  username?: string;

  @ApiPropertyOptional({ description: 'API描述（模糊搜索）' })
  @IsOptional()
  @IsString()
  apiDescription?: string;

  @ApiPropertyOptional({ description: 'API路径（模糊搜索）' })
  @IsOptional()
  @IsString()
  apiPath?: string;

  @ApiPropertyOptional({ description: 'API方法', example: 'GET' })
  @IsOptional()
  @IsString()
  apiMethod?: string;

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
