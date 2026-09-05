package com.hcsy.spring.entity.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 网关认证通过后返回的身份信息
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class AuthIdentityDTO {
    private Long userId;
    private String username;
    private String sessionId;
}
