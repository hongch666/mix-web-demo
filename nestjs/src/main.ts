import { ConfigService } from "@nestjs/config";
import { Transport } from "@nestjs/microservices";
import { join } from "node:path";
import { NestFastifyApplication } from "@nestjs/platform-fastify";
import { createApp } from "./app";

async function bootstrap(): Promise<void> {
  // 初始化app
  const app: NestFastifyApplication = await createApp();
  // 获取 NestJS 服务的端口和IP
  const configService: ConfigService<unknown, boolean> = app.get(ConfigService);
  const port: number = configService.get<number>("server.port")!;
  const ip: string = configService.get<string>("server.ip")!;
  const grpcEnabled: boolean = configService.get<boolean>("grpc.enabled") ?? true;
  if (grpcEnabled) {
    app.connectMicroservice({
      transport: Transport.GRPC,
      options: {
        package: ["common.v1", "nestjs.v1"],
        protoPath: [
          join(process.cwd(), "../proto/common/result.proto"),
          join(process.cwd(), "../proto/nestjs/log.proto"),
          join(process.cwd(), "../proto/nestjs/email.proto"),
        ],
        url: `${ip}:${configService.get<number>("grpc.port")!}`,
        loader: { keepCase: true, defaults: true, oneofs: true },
      },
    });
    await app.startAllMicroservices();
  }
  // 监听服务
  await app.listen(port, ip);
}

bootstrap();
