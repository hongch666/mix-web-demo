package com.hcsy.spring.core.properties;

import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.validation.annotation.Validated;

@Configuration
@ConfigurationProperties(prefix = "user")
@Validated
public class UserPasswordProperties {

    @NotBlank(message = "USER_DEFAULT_PASSWORD 不能为空")
    private String defaultPassword;

    @NotBlank(message = "USER_RESET_PASSWORD 不能为空")
    private String resetPassword;

    public String getDefaultPassword() {
        return defaultPassword;
    }

    public void setDefaultPassword(String defaultPassword) {
        this.defaultPassword = defaultPassword;
    }

    public String getResetPassword() {
        return resetPassword;
    }

    public void setResetPassword(String resetPassword) {
        this.resetPassword = resetPassword;
    }
}
