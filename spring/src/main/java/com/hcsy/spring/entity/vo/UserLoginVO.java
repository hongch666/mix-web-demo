package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserLoginVO {
    private String token; // JWT 令牌
    private Long userId; // 用户ID
    private String username; // 用户名
    private Long onlineDeviceCount; // 在线设备数
}
