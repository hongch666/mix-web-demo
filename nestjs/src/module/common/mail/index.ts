// module/common/mail 目录的公开出口，跨目录引用统一从此处导入
export { MailController } from "./mail.controller";
export { MailModule } from "./mail.module";
export { MailService } from "./mail.service";
export { MAIL_TRANSPORTER } from "./mail.tokens";
