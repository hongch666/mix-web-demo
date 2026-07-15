import { Body, Controller, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { ApiResponse, success } from "src/common/utils/response";
import { RequireInternalToken } from "src/framework/decorators/requireInternalToken.decorator";
import { InternalEmailCodeSendDto } from "./dto/mail.dto";
import { MailService } from "./mail.service";

@Controller("email")
@ApiTags("邮件模块")
export class MailController {
  constructor(private readonly mailService: MailService) {}

  @Post("send-code")
  @RequireInternalToken("spring")
  @ApiOperation({
    summary: "发送邮箱验证码",
    description: "通过 SMTP 发送验证码邮件",
  })
  async sendEmailCode(
    @Body() dto: InternalEmailCodeSendDto,
  ): Promise<ApiResponse<null>> {
    // 不 await，邮件异步发送，避免 SMTP 耗时导致调用方超时
    this.mailService.sendVerificationCode(dto);
    return success(null);
  }
}
