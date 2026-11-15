import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document } from "mongoose";
import { Defaults } from "src/common/constants";

export type LogDeletionDocument = LogDeletion & Document;

/**
 * 日志删除墓碑 MongoDB 文档结构，记录被删除日志的主键与原产生时间，供数仓同步清除
 */
@Schema({ timestamps: true })
export class LogDeletion {
  // 日志类型标识，取值见 LogTypes
  @Prop({ required: true })
  logType!: string;

  // 被删除日志的 MongoDB 主键，数仓按此删除 ODS 行
  @Prop({ required: true })
  eventId!: string;

  // 原日志的产生时间，数仓据此定位受影响的月份分区
  @Prop({ type: Date, required: true })
  logCreatedAt!: Date;

  // 墓碑写入时间，TTL 索引按此回收
  @Prop()
  createdAt?: Date;

  // 墓碑更新时间
  @Prop()
  updatedAt?: Date;
}

export const LogDeletionSchema = SchemaFactory.createForClass(LogDeletion);

// 同一日志重复删除只保留一条墓碑，数仓按主键删除天然幂等
LogDeletionSchema.index(
  { eventId: 1, logType: 1 },
  { name: "eventId_1_logType_1", unique: true },
);
// 墓碑只服务于删除向数仓的传播，过期后自动回收，数仓残留由保留期清理兜底
LogDeletionSchema.index(
  { createdAt: 1 },
  {
    name: "createdAt_ttl",
    expireAfterSeconds: Defaults.LOG_DELETION_TTL_SECONDS,
  },
);
