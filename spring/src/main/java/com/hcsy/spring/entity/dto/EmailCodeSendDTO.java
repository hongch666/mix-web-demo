package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 发送邮箱验证码请求，携带收件邮箱及 register、login 或 reset 使用场景
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "发送邮箱验证码请求")
public class EmailCodeSendDTO {
    @Schema(description = "收件邮箱")
    @Email(message = "邮箱格式不正确")
    private String email;

    @Schema(description = "验证码场景，register、login 或 reset")
    private String type;
}
