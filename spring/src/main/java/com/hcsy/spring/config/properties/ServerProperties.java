package com.hcsy.spring.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

/**
 * 服务端配置属性（构造器绑定，不可变）
 *
 * @param mode 运行模式标识（如 dev/prod），用于区分环境相关行为
 * @param port 服务端口
 * @param address 服务监听地址，启动日志中的服务地址与 Swagger 地址直接使用该值
 */
@ConfigurationProperties(prefix = "server")
public record ServerProperties(@DefaultValue("dev") String mode, @DefaultValue("8081") int port,
    @DefaultValue("0.0.0.0") String address) {
}
