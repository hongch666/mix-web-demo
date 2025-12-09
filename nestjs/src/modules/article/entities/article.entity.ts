import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';

@Entity('articles')
export class Articles {
  @ApiProperty({ description: '文章ID', example: 1 })
  @PrimaryGeneratedColumn()
  id: number;

  @ApiProperty({ description: '标题', example: '我的第一篇文章' })
  @Column({ length: 255 })
  title: string;

  @ApiProperty({ description: '内容', example: '这是文章内容' })
  @Column('text')
  content: string;

  @ApiProperty({ description: '用户ID', example: 1001 })
  @Column()
  user_id: number;

  @ApiProperty({ description: '标签', example: 'nestjs' })
  @Column({ length: 255 })
  tags: string;

  @ApiProperty({ description: '状态', example: 0 })
  @Column({ type: 'tinyint' })
  status: number;

  @ApiProperty({ description: '浏览量', example: 123, default: 0 })
  @Column({ type: 'int', default: 0 })
  views: number;

  @ApiProperty({ description: '子分类ID', example: 1 })
  @Column({ type: 'int', name: 'sub_category_id' })
  sub_category_id: number;

  @ApiProperty({ description: '创建时间', example: '2024-06-17T12:00:00.000Z' })
  @CreateDateColumn({ name: 'create_at' })
  create_at: Date;

  @ApiProperty({ description: '更新时间', example: '2024-06-17T12:00:00.000Z' })
  @UpdateDateColumn({ name: 'update_at' })
  update_at: Date;
}
