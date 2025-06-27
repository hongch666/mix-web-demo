import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity('user')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 100 })
  name: string;

  @Column({ type: 'int', nullable: true })
  age: number;

  @Column()
  password: string;

  @Column({ nullable: true })
  email: string;

  @Column()
  role: string;
}
