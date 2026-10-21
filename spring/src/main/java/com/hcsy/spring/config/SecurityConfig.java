package com.hcsy.spring.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

/**
 * 装配用于用户密码加密与校验的 BCrypt 编码器
 */
@Configuration
public class SecurityConfig {

    /**
     * 装配用于用户密码加密与校验的 BCrypt 编码器
     */
    @Bean
    BCryptPasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
