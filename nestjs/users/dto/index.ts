import { ApiProperty } from '@nestjs/swagger';
import {
  IsNotEmpty,
  IsString,
  Length,
  IsEmail,
  IsInt,
  Min,
  Max,
} from 'class-validator';

export class UserCreateDTO {
  @ApiProperty({
    required: true,
  })
  @IsNotEmpty({ message: '密码不能为空' })
  @IsString({ message: '密码必须是字符串' })
  @Length(3, 20, { message: '密码长度必须在3到20个字符之间' })
  password: string;

  @ApiProperty({
    required: true,
  })
  @IsNotEmpty({ message: '用户名不能为空' })
  @IsString({ message: '用户名必须是字符串' })
  @Length(3, 20, { message: '用户名长度必须在3到20个字符之间' })
  name: string;

  @ApiProperty({
    required: true,
  })
  @IsNotEmpty({ message: '年龄不能为空' })
  @IsInt({ message: '年龄必须是整数' })
  @Min(0, { message: '年龄不能小于0' })
  @Max(150, { message: '年龄不能超过150' })
  age: number;

  @ApiProperty({
    required: true,
  })
  @IsNotEmpty({ message: '邮箱不能为空' })
  @IsEmail({}, { message: '邮箱格式不正确' })
  email: string;
}

export class UserUpdateDTO extends UserCreateDTO {
  @ApiProperty({
    required: true,
  })
  @IsNotEmpty({ message: 'id不能为空' })
  @IsInt({ message: 'id必须是整数' })
  @Min(0, { message: 'id不能小于0' })
  id: number;
}
