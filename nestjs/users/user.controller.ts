// src/user/user.controller.ts
import {
  Controller,
  Get,
  Post,
  Body,
  Delete,
  Param,
  ParseIntPipe,
  Put,
} from '@nestjs/common';
import { UserService } from './user.service';
import { User } from './entity/user.entity';
import { ApiOperation, ApiParam, ApiTags } from '@nestjs/swagger';
import { UserCreateDTO, UserUpdateDTO } from './dto';

@Controller('users')
@ApiTags('测试模块')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get()
  @ApiOperation({ summary: '获取用户信息', description: '获取用户信息列表' })
  findAll(): Promise<User[]> {
    return this.userService.findAll();
  }

  @Post()
  @ApiOperation({ summary: '新增用户', description: '通过请求体创建用户信息' })
  create(@Body() userDto: UserCreateDTO) {
    return this.userService.create(userDto);
  }

  @Delete(':id')
  @ApiOperation({ summary: '删除用户', description: '根据ID删除用户' })
  @ApiParam({ name: 'id', type: Number, description: '用户ID' })
  remove(@Param('id', ParseIntPipe) id: number) {
    return this.userService.remove(id);
  }

  @Get(':id')
  @ApiOperation({
    summary: '根据ID获取用户',
    description: '根据用户ID获取信息',
  })
  @ApiParam({ name: 'id', type: Number, description: '用户ID' })
  findOne(@Param('id', ParseIntPipe) id: number): Promise<User> {
    return this.userService.findOne(id);
  }

  @Put()
  @ApiOperation({ summary: '修改用户', description: '通过请求体修改用户信息' })
  update(@Body() userDto: UserUpdateDTO) {
    return this.userService.update(userDto);
  }
}
