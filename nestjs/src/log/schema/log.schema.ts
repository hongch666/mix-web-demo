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
  @Prop({ enum: ['add', 'search', 'edit', 'delete'], required: true })
  action: string;

  // 操作内容（任意 JSON 对象）
  @Prop({ type: Object, required: true })
  content: Record<string, any>;

  // 操作说明（可选）
  @Prop()
  msg?: string;
}

export const ArticleLogSchema = SchemaFactory.createForClass(ArticleLog);
