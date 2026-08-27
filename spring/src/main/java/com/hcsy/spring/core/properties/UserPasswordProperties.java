package com.hcsy.spring.core.properties;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import com.hcsy.spring.common.constants.Messages;

import jakarta.validation.constraints.NotBlank;

/**
 * 用户密码配置属性（构造器绑定，不可变）
 *
 * @param defaultPassword 默认密码
 * @param resetPassword   重置密码
 */
@ConfigurationProperties(prefix = "user")
@Validated
public record UserPasswordProperties(
        @NotBlank(message = Messages.USER_DEFAULT_PASSWORD_NOT_BLANK) String defaultPassword,
        @NotBlank(message = Messages.USER_RESET_PASSWORD_NOT_BLANK) String resetPassword) {
}
