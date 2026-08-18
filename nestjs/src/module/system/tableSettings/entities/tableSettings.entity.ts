import { ApiProperty } from "@nestjs/swagger";
import {
  Column,
  CreateDateColumn,
  Entity,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from "typeorm";

@Entity("user_table_settings")
export class TableSettings {
  @ApiProperty({ description: "设置ID", example: 1 })
  @PrimaryGeneratedColumn()
  id!: number;

  @ApiProperty({ description: "用户ID", example: 1 })
  @Column({ name: "user_id", type: "bigint" })
  user_id!: number;

  @ApiProperty({ description: "页面标识", example: "articles" })
  @Column({ name: "table_key", type: "varchar", length: 64 })
  table_key!: string;

  @ApiProperty({ description: "列配置JSON" })
  @Column({ type: "json" })
  columns!: object;

  @ApiProperty({ description: "创建时间" })
  @CreateDateColumn({ name: "create_at", type: "datetime" })
  create_at!: Date;

  @ApiProperty({ description: "更新时间" })
  @UpdateDateColumn({ name: "update_at", type: "datetime" })
  update_at!: Date;
}
