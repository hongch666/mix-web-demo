import { Module } from "@nestjs/common";
import { ClientModule } from "src/module/common/client/client.module";
import { TestController } from "./test.controller";

@Module({
  imports: [ClientModule],
  controllers: [TestController],
  providers: [],
})
export class TestModule {}
