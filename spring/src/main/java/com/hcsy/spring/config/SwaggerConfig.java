package com.hcsy.spring.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;

import java.util.List;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Spring部分的Swagger文档集成")
                        .version("1.0.0")
                        .description("这是demo项目的Spring部分的Swagger文档集成"))
                .servers(List.of(
                        new Server().url("http://localhost:8081").description("baseURL")));
    }
}
