import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type ArticleLogDocument = ArticleLog & Document;

@Schema({ timestamps: true }) // 自动添加 createdAt 和 updatedAt
export class ArticleLog {
  // 用户ID（MySQL 表的自增主键，数字）
  @Prop({ type: Number, required: true })
  userId: number;

  // 文章ID（MySQL 表的自增主键，数字）
  @Prop({ type: Number, required: true })
  articleId: number;

  // 操作类型
  @Prop({ required: true })
  action: string;

  // 操作内容（任意 JSON 对象）
  @Prop({ type: Object, required: true })
  content: Record<string, any>;

  // 操作说明（可选）
  @Prop()
  msg?: string;
  // 声明 create_at 字段，类型为 Date
  @Prop()
  createdAt?: Date;

  // 声明 update_at 字段，类型为 Date
  @Prop()
  updatedAt?: Date;
}

export const ArticleLogSchema = SchemaFactory.createForClass(ArticleLog);

// 添加关键索引以提高查询性能
ArticleLogSchema.index({ createdAt: -1 });
ArticleLogSchema.index({ userId: 1, createdAt: -1 });
ArticleLogSchema.index({ articleId: 1, createdAt: -1 });
ArticleLogSchema.index({ action: 1, createdAt: -1 });
