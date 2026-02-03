package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import com.fasterxml.jackson.annotation.JsonProperty;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserVO {
    private Long id;
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String password;
    private String name;
    private Integer age;
    private String email;
    private String role;
    private String img;
    private String signature;
    // 分页查询时返回这两个字段
    private Integer loginStatus; // 登录状态，1表示在线，0表示离线
    private Long onlineDeviceCount; // 在线设备数
}
