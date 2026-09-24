package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * NestJS 内部邮件发送 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "内部发送验证码邮件请求")
public class InternalEmailCodeSendDTO {

    /**
     * 收件邮箱
     */
    @Schema(description = "收件邮箱")
    private String email;

    /**
     * 验证码
     */
    @Schema(description = "验证码")
    private String code;

    /**
     * 验证码场景（register/login/reset）
     */
    @Schema(description = "验证码场景，register、login 或 reset")
    private String type;

    /**
     * 过期时间（分钟），默认 10
     */
    @Schema(description = "验证码过期时间，单位分钟")
    private Integer expireMinutes;
}
