import { ConfigModule, ConfigService } from "@nestjs/config";
import { Module, Provider } from "@nestjs/common";
import * as nodemailer from "nodemailer";
import { MailController } from "./mail.controller";
import { MailService } from "./mail.service";

export const MAIL_TRANSPORTER = Symbol("MAIL_TRANSPORTER");

const mailTransporterProvider: Provider = {
  provide: MAIL_TRANSPORTER,
  inject: [ConfigService],
  useFactory: (configService: ConfigService): nodemailer.Transporter | null => {
    const username: string | undefined =
      configService.get<string>("mail.username");
    const password: string | undefined =
      configService.get<string>("mail.password");
    if (!username || !password) {
      return null;
    }

    const timeout: number = Math.max(
      15000,
      Number(configService.get<string>("mail.timeout")) || 10000,
    );
    const secureValue: unknown = configService.get<unknown>("mail.secure");
    return nodemailer.createTransport({
      host: configService.get<string>("mail.host"),
      port: Number(configService.get<string>("mail.port")),
      secure:
        secureValue === true || secureValue === "true" || secureValue === "1",
      connectionTimeout: timeout,
      greetingTimeout: timeout,
      socketTimeout: timeout,
      auth: { user: username, pass: password },
    });
  },
};

@Module({
  imports: [ConfigModule],
  controllers: [MailController],
  providers: [mailTransporterProvider, MailService],
})
export class MailModule {}
