package com.hcsy.spring.common.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;

import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.hcsy.spring.common.utils.Constants;

@Configuration
public class SwaggerConfig {

    @Value("${server.port}")
    private String port;

    @Bean
    OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title(Constants.SWAGGER_TITLE)
                .version(Constants.SWAGGER_VERSION)
                .description(Constants.SWAGGER_DESC))
            .servers(List.of(
                new Server().url(Constants.SWAGGER_URL_PREFIX + port).description("baseURL")));
    }
}
