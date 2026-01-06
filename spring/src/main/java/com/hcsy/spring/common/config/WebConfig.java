package com.hcsy.spring.common.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.hcsy.spring.common.interceptor.UserInfoInterceptor;

import lombok.RequiredArgsConstructor;

@Configuration
@RequiredArgsConstructor
public class WebConfig implements WebMvcConfigurer {

    private final UserInfoInterceptor userInfoInterceptor;

    @SuppressWarnings("null")
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(userInfoInterceptor)
                .addPathPatterns("/**") // 拦截所有路径
                .excludePathPatterns("/public/**", "/swagger-ui/**"); // 可以排除无需认证的路径
    }
}
