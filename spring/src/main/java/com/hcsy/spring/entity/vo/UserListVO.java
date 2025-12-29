package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 用户列表返回对象
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserListVO {
    /**
     * 总记录数
     */
    private Long total;

    /**
     * 用户列表
     */
    private List<UserVO> list;
}
