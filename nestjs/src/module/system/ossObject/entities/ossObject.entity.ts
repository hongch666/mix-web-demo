import { ApiProperty } from "@nestjs/swagger";
import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
  Unique,
  UpdateDateColumn,
} from "typeorm";

/**
 * OSS 对象账本实体，记录每次上传产生的对象及其来源，供定时清理判断是否存在在用引用
 */
@Entity("oss_object")
@Unique("uk_oss_object_key", ["oss_key"])
@Index("idx_oss_object_created_at", ["create_at"])
@Index("idx_oss_object_prefix_type", ["prefix_type"])
export class OssObject {
  @ApiProperty({ description: "账本ID", example: 1 })
  @PrimaryGeneratedColumn()
  id!: number;

  @ApiProperty({
    description: "OSS 对象 key（不含域名）",
    example: "pic/a.png",
  })
  @Column({ name: "oss_key", type: "varchar", length: 512 })
  oss_key!: string;

  @ApiProperty({ description: "OSS 对象完整访问 URL" })
  @Column({ name: "oss_url", type: "varchar", length: 1024 })
  oss_url!: string;

  @ApiProperty({ description: "key 前缀类型", example: "pic" })
  @Column({ name: "prefix_type", type: "varchar", length: 32 })
  prefix_type!: string;

  @ApiProperty({ description: "上传来源", example: "user_image" })
  @Column({ name: "source", type: "varchar", length: 32 })
  source!: string;

  @ApiProperty({ description: "上传用户ID，匿名上传为空", required: false })
  @Column({ name: "uploader_user_id", type: "bigint", nullable: true })
  uploader_user_id!: number | null;

  @ApiProperty({ description: "对象字节数", required: false })
  @Column({ name: "file_size", type: "bigint", nullable: true })
  file_size!: number | null;

  @ApiProperty({ description: "最近一次扫描确认在用的时间", required: false })
  @Column({ name: "last_verified_at", type: "datetime", nullable: true })
  last_verified_at!: Date | null;

  @ApiProperty({ description: "创建时间" })
  @CreateDateColumn({ name: "create_at", type: "datetime" })
  create_at!: Date;

  @ApiProperty({ description: "更新时间" })
  @UpdateDateColumn({ name: "update_at", type: "datetime" })
  update_at!: Date;
}
