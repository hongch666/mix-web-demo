import { ApiProperty } from '@nestjs/swagger';
import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';

@Entity('user')
export class User {
  @ApiProperty({ description: '用户ID', example: 1 })
  @PrimaryGeneratedColumn()
  id!: number;

  @ApiProperty({ description: '用户名', example: 'hcsy' })
  @Column({ length: 100 })
  name!: string;

  @ApiProperty({ description: '年龄', example: 30, nullable: true })
  @Column({ type: 'int', nullable: true })
  age!: number;

  @ApiProperty({ description: '密码', example: 'password123' })
  @Column()
  password!: string;

  @ApiProperty({ description: '邮箱', example: 'hcsy@example.com' })
  @Column({ nullable: true })
  email!: string;

  @ApiProperty({ description: '角色', example: 'user' })
  @Column()
  role!: string;

  @ApiProperty({
    description: '头像',
    example: 'https://example.com/avatar.jpg',
    nullable: true,
  })
  @Column({ nullable: true })
  img!: string;

  @ApiProperty({ description: '签名', example: '我是程序员', nullable: true })
  @Column({ type: 'varchar', length: 255, nullable: true })
  signature!: string;
}
