import { Module } from "@nestjs/common";
import { SqlToolsController } from "./sqlTools.controller";
import { SqlToolsService } from "./sqlTools.service";

@Module({
  controllers: [SqlToolsController],
  providers: [SqlToolsService],
  exports: [SqlToolsService],
})
export class SqlToolsModule {}
