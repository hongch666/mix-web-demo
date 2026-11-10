import { Prop, Schema, SchemaFactory } from "@nestjs/mongoose";
import { Document } from "mongoose";

export type ApiLogDocument = ApiLog & Document;

/**
 * API 日志 MongoDB 文档结构，记录接口调用的用户、路径、方法与响应时间并声明查询索引
 */
@Schema({ timestamps: true }) // 自动添加 createdAt 和 updatedAt
export class ApiLog {
  // 用户ID
  @Prop({ type: Number, required: true })
  userId!: number;

  // 用户名
  @Prop({ required: true })
  username!: string;

  // API 描述
  @Prop({ required: true })
  apiDescription!: string;

  // API 路径
  @Prop({ required: true })
  apiPath!: string;

  // API 路径小写副本，用于大小写无关的前缀检索
  @Prop({ required: true })
  apiPathLower!: string;

  // API 方法（GET、POST 等）
  @Prop({ required: true })
  apiMethod!: string;

  // 查询参数（任意 JSON 对象）
  @Prop({ type: Object })
  queryParams!: Record<string, unknown>;

  // 路径参数（任意 JSON 对象）
  @Prop({ type: Object })
  pathParams!: Record<string, unknown>;

  // 请求体（任意 JSON 对象）
  @Prop({ type: Object })
  requestBody!: Record<string, unknown>;

  // 接口响应时间
  @Prop({ type: Number, required: true })
  responseTime!: number;

  // 声明 create_at 字段，类型为 Date
  @Prop()
  createdAt?: Date;

  // 声明 update_at 字段，类型为 Date
  @Prop()
  updatedAt?: Date;
}

export const ApiLogSchema = SchemaFactory.createForClass(ApiLog);

// 添加关键索引以提高查询性能
ApiLogSchema.index({ userId: 1, createdAt: -1 });
ApiLogSchema.index({ createdAt: -1 });
// 路径模糊搜索改用小写副本的前缀匹配，原始 apiPath 上的复合索引永远走不到
ApiLogSchema.index({ apiPathLower: 1, createdAt: -1 });
ApiLogSchema.index({ userId: 1, apiMethod: 1, createdAt: -1 });
// 只按 apiMethod 过滤时上面的复合索引以 userId 打头用不上，单独补一条
ApiLogSchema.index({ apiMethod: 1, createdAt: -1 });
// 深分页改走 createdAt + _id 游标，排序键必须进复合索引才能避免同毫秒内的内存排序
ApiLogSchema.index({ createdAt: -1, _id: -1 }, { name: "createdAt_-1__id_-1" });
