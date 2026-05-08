import { ApiProperty } from "@nestjs/swagger";
import {
  Column,
  CreateDateColumn,
  Entity,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from "typeorm";

@Entity("user")
export class User {
  @ApiProperty({ description: "用户ID", example: 1 })
  @PrimaryGeneratedColumn()
  id!: number;

  @ApiProperty({ description: "用户名", example: "hcsy" })
  @Column({ length: 100 })
  name!: string;

  @ApiProperty({ description: "年龄", example: 30, nullable: true })
  @Column({ type: "int", nullable: true })
  age!: number | null;

  @ApiProperty({ description: "密码", example: "password123" })
  @Column()
  password!: string;

  @ApiProperty({ description: "邮箱", example: "hcsy@example.com" })
  @Column({ type: "varchar", length: 255, nullable: true })
  email!: string | null;

  @ApiProperty({ description: "角色", example: "user" })
  @Column()
  role!: string;

  @ApiProperty({
    description: "头像",
    example: "https://example.com/avatar.jpg",
    nullable: true,
  })
  @Column({ type: "varchar", length: 255, nullable: true })
  img!: string | null;

  @ApiProperty({ description: "签名", example: "我是程序员", nullable: true })
  @Column({ type: "varchar", length: 255, nullable: true })
  signature!: string | null;

  @ApiProperty({
    description: "GitHub用户ID",
    example: "123456",
    nullable: true,
  })
  @Column({ name: "github_id", type: "bigint", nullable: true, unique: true })
  githubId!: string | null;

  @ApiProperty({
    description: "GitHub登录名",
    example: "octocat",
    nullable: true,
  })
  @Column({
    name: "github_login",
    type: "varchar",
    length: 255,
    nullable: true,
  })
  githubLogin!: string | null;

  @ApiProperty({
    description: "GitHub主页地址",
    example: "https://github.com/octocat",
    nullable: true,
  })
  @Column({ name: "github_url", type: "varchar", length: 255, nullable: true })
  githubUrl!: string | null;

  @ApiProperty({ description: "注册来源", example: "github" })
  @Column({
    name: "auth_provider",
    type: "varchar",
    length: 50,
    default: "local",
  })
  authProvider!: string;

  @ApiProperty({
    description: "最近登录时间",
    example: "2026-05-04T12:00:00.000Z",
    nullable: true,
  })
  @Column({ name: "last_login_at", type: "datetime", nullable: true })
  lastLoginAt!: Date | null;

  @ApiProperty({
    description: "创建时间",
    example: "2026-05-04T12:00:00.000Z",
    nullable: true,
  })
  @CreateDateColumn({ name: "create_at", type: "datetime" })
  createAt!: Date;

  @ApiProperty({
    description: "更新时间",
    example: "2026-05-04T12:00:00.000Z",
    nullable: true,
  })
  @UpdateDateColumn({ name: "update_at", type: "datetime" })
  updateAt!: Date;
}
