package com.hcsy.spring.config.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import com.hcsy.spring.common.constants.Messages;

import jakarta.validation.constraints.NotBlank;

/**
 * 用户密码配置属性（构造器绑定，不可变）
 *
 * @param defaultPassword 默认密码，同时用于创建用户未指定密码与管理员重置未指定密码的场景
 */
@ConfigurationProperties(prefix = "user")
@Validated
public record UserPasswordProperties(
    @NotBlank(message = Messages.USER_DEFAULT_PASSWORD_NOT_BLANK) String defaultPassword) {
}
