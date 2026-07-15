import { Module } from "@nestjs/common";
import { ClientModule } from "src/module/common/client/client.module";
import { TaskModule } from "src/module/common/task/task.module";
import { TestController } from "./test.controller";

@Module({
  imports: [ClientModule, TaskModule],
  controllers: [TestController],
  providers: [],
})
export class TestModule {}
