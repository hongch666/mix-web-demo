import { Module } from "@nestjs/common";
import { MongoToolsController } from "./mongoTools.controller";
import { MongoToolsService } from "./mongoTools.service";

@Module({
  providers: [MongoToolsService],
  controllers: [MongoToolsController],
  exports: [MongoToolsService],
})
export class MongoToolsModule {}
