import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type ApiLogDocument = ApiLog & Document;

@Schema({ timestamps: true }) // 自动添加 createdAt 和 updatedAt
export class ApiLog {
  // 用户ID
  @Prop({ type: Number, required: true })
  userId: number;

  // 用户名
  @Prop({ required: true })
  username: string;

  // API 描述
  @Prop({ required: true })
  apiDescription: string;

  // API 路径
  @Prop({ required: true })
  apiPath: string;

  // API 方法（GET、POST 等）
  @Prop({ required: true })
  apiMethod: string;

  // 查询参数（任意 JSON 对象）
  @Prop({ type: Object })
  queryParams: Record<string, any>;

  // 路径参数（任意 JSON 对象）
  @Prop({ type: Object })
  pathParams: Record<string, any>;

  // 请求体（任意 JSON 对象）
  @Prop({ type: Object })
  requestBody: Record<string, any>;

  // 接口响应时间
  @Prop({ type: Number, required: true })
  responseTime: number;

  // 声明 create_at 字段，类型为 Date
  @Prop()
  createdAt?: Date;

  // 声明 update_at 字段，类型为 Date
  @Prop()
  updatedAt?: Date;
}

export const ApiLogSchema = SchemaFactory.createForClass(ApiLog);
