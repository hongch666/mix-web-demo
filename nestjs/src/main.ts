import { Logger } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import { NestFastifyApplication } from "@nestjs/platform-fastify";
import { createApp } from "./app";
import { Messages } from "./common/constants";

async function bootstrap(): Promise<void> {
  // 初始化app
  const app: NestFastifyApplication = await createApp();
  // 获取 NestJS 服务的端口和IP
  const configService: ConfigService<unknown, boolean> = app.get(ConfigService);
  const port: number = configService.get<number>("server.port")!;
  const ip: string = configService.get<string>("server.ip")!;
  // 监听服务
  await app.listen(port, ip);
}

// 启动失败时以非零状态码退出，避免进程静默存活
void bootstrap().catch((error: unknown) => {
  Logger.error(Messages.SERVER_START_FAILED, error, "Bootstrap");
  process.exit(1);
});
