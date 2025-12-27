package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class FocusUserVO {
    private Long id; // 用户ID
    private String name; // 用户名
    private Integer age; // 年龄
    private String email; // 邮箱
    private String img; // 头像
    private String signature; // 签名
    private String role; // 角色
    private LocalDateTime focusedTime; // 关注时间
}
