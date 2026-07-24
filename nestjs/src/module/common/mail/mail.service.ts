import { Injectable, Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import * as nodemailer from "nodemailer";
import { Messages } from "src/common/constants";
import { InternalEmailCodeSendDto } from "./dto/mail.dto";
import { buildEmailContent } from "./templates/mail.template";

@Injectable()
export class MailService {
  private readonly logger = new Logger(MailService.name);
  private transporter!: nodemailer.Transporter;

  constructor(private readonly configService: ConfigService) {
    const host: string | undefined =
      this.configService.get<string>("mail.host");
    const port: string | undefined =
      this.configService.get<string>("mail.port");
    const secureVal: string | undefined =
      this.configService.get<string>("mail.secure");
    const username: string | undefined =
      this.configService.get<string>("mail.username");
    const password: string | undefined =
      this.configService.get<string>("mail.password");

    if (!username || !password) {
      this.logger.warn(Messages.MAIL_SERVICE_CONFIG_INCOMPLETE);
      return;
    }

    this.transporter = nodemailer.createTransport({
      host,
      port: Number(port),
      secure: secureVal === "true" || secureVal === "1",
      auth: {
        user: username,
        pass: password,
      },
    });
  }

  async sendVerificationCode(dto: InternalEmailCodeSendDto): Promise<void> {
    const { email, code, type, expireMinutes = 10 } = dto;

    // 脱敏记录日志，不打印完整验证码
    const maskedEmail: string = email.replace(/(.{3}).+(.{2}@)/, "$1***$2");
    this.logger.log(Messages.VERIFICATION_CODE_EMAIL_SENDING(maskedEmail, type));

    if (!this.transporter) {
      throw new Error(Messages.MAIL_SERVICE_CONFIG_INCORRECT);
    }

    const from: string | undefined =
      this.configService.get<string>("mail.from") ||
      this.configService.get<string>("mail.username");

    // 异步发送邮件，不阻塞调用方，发送结果通过日志记录，不影响主流程
    this.transporter
      .sendMail({
        from: `"MixWeb" <${from}>`,
        to: email,
        subject: this.getSubject(type),
        html: buildEmailContent(code, type, expireMinutes),
      })
      .then((): void => {
        this.logger.log(Messages.VERIFICATION_CODE_EMAIL_SENT(maskedEmail));
      })
      .catch((error: unknown) => {
        this.logger.error(
          Messages.VERIFICATION_CODE_EMAIL_FAILED(maskedEmail),
          error instanceof Error ? error.message : String(error),
        );
      });
  }

  private getSubject(type: string): string {
    switch (type) {
      case "register":
        return Messages.EMAIL_VERIFICATION_CODE_REGISTER_SUBJECT;
      case "login":
        return Messages.EMAIL_VERIFICATION_CODE_LOGIN_SUBJECT;
      case "reset":
        return Messages.EMAIL_VERIFICATION_CODE_RESET_SUBJECT;
      default:
        return Messages.EMAIL_VERIFICATION_CODE_SUBJECT;
    }
  }
}
