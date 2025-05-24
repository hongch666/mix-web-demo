import { Controller, Get, Post, Query, Param, Body, Req } from '@nestjs/common';
import { NacosService } from '../nacos/nacos.service';
import { success, error } from "../utils/response";

@Controller('api_nestjs')
export class ClientController {
    constructor(private readonly nacosService: NacosService) {}

    @Get('nestjs')
    async getNestjs():Promise<any>{
        return success("Hello,I am Nest.js!")
    }

    @Get('spring')
    async getSpring():Promise<any>{
        return this.nacosService.call({
            serviceName: 'spring',
            method: 'GET',
            path: '/api_spring/spring'
        })
    }

    @Get('gin')
    async getGin():Promise<any>{
        return this.nacosService.call({
            serviceName: 'gin',
            method: 'GET',
            path: '/api_gin/gin'
        })
    }
}
