import { ApiProperty } from "@nestjs/swagger";
import {
  IsEmail,
  IsIn,
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  Min,
} from "class-validator";
import { Messages } from "src/common/constants";
import { ExposeName } from "src/common/utils/snakeCase";

/**
 * 内部服务发送邮箱验证码的请求体，包含收件邮箱、验证码、场景类型与可选过期分钟数
 */
export class InternalEmailCodeSendDto {
  @ApiProperty({ description: "收件邮箱", example: "user@example.com" })
  @IsEmail({}, { message: Messages.DTO_EMAIL_FORMAT_INVALID })
  @IsNotEmpty({ message: Messages.DTO_EMAIL_NOT_EMPTY })
  email!: string;

  @ApiProperty({ description: "验证码", example: "123456" })
  @IsString({ message: Messages.DTO_VERIFICATION_CODE_MUST_BE_STRING })
  @IsNotEmpty({ message: Messages.DTO_VERIFICATION_CODE_NOT_EMPTY })
  code!: string;

  @ApiProperty({
    description: "验证码场景",
    example: "register",
    enum: ["register", "login", "reset"],
  })
  @IsIn(["register", "login", "reset"], {
    message: Messages.DTO_VERIFICATION_CODE_TYPE_INVALID,
  })
  @IsNotEmpty({ message: Messages.DTO_VERIFICATION_CODE_TYPE_NOT_EMPTY })
  type!: string;

  @ApiProperty({
    description: "过期时间（分钟）",
    example: 10,
    required: false,
  })
  @ExposeName()
  @IsOptional()
  @IsInt({ message: Messages.DTO_EXPIRE_MINUTES_MUST_BE_INT })
  @Min(1, { message: Messages.DTO_EXPIRE_MINUTES_TOO_SMALL })
  expireMinutes?: number;
}
