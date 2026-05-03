package com.hcsy.spring.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * NestJS 内部邮件发送 DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class InternalEmailCodeSendDTO {

    /**
     * 收件邮箱
     */
    private String email;

    /**
     * 验证码
     */
    private String code;

    /**
     * 验证码场景（register/login/reset）
     */
    private String type;

    /**
     * 过期时间（分钟），默认 10
     */
    private Integer expireMinutes;
}
