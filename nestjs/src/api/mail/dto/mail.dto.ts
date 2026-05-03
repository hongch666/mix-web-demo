import {
  IsEmail,
  IsIn,
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  Min,
} from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class InternalEmailCodeSendDto {
  @ApiProperty({ description: '收件邮箱', example: 'user@example.com' })
  @IsEmail({}, { message: '邮箱格式不正确' })
  @IsNotEmpty({ message: '邮箱不能为空' })
  email!: string;

  @ApiProperty({ description: '验证码', example: '123456' })
  @IsString({ message: '验证码必须是字符串' })
  @IsNotEmpty({ message: '验证码不能为空' })
  code!: string;

  @ApiProperty({
    description: '验证码场景',
    example: 'register',
    enum: ['register', 'login', 'reset'],
  })
  @IsIn(['register', 'login', 'reset'], {
    message: '验证码类型只能是 register、login 或 reset',
  })
  @IsNotEmpty({ message: '验证码类型不能为空' })
  type!: string;

  @ApiProperty({
    description: '过期时间（分钟）',
    example: 10,
    required: false,
  })
  @IsOptional()
  @IsInt({ message: '过期时间必须是整数' })
  @Min(1, { message: '过期时间不能小于 1 分钟' })
  expireMinutes?: number;
}
