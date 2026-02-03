package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserListVO {
    private Long total; // 总记录数
    private List<UserVO> list; // 用户列表
}
