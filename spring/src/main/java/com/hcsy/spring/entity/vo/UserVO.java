package com.hcsy.spring.entity.vo;

import lombok.Data;

@Data
public class UserVO {
    private Long id;
    private String password;
    private String name;
    private Integer age;
    private String email;
    private String role;
    private String img;
    // 分页查询时返回这两个字段
    private Integer loginStatus; // 登录状态，1表示在线，0表示离线
    private Long onlineDeviceCount; // 在线设备数
}
