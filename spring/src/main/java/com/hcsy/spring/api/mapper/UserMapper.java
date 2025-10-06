package com.hcsy.spring.api.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.User;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 继承 BaseMapper 自动拥有基本的 CRUD 方法

    /**
     * 根据用户名模糊查询用户，并按登录状态排序后分页
     * 
     * @param username       用户名（可选，用于模糊查询）
     * @param loginStatusMap 用户ID到登录状态的映射
     * @param offset         分页偏移量
     * @param pageSize       每页大小
     * @return 用户列表
     */
    List<User> selectUsersWithLoginStatus(
            @Param("username") String username,
            @Param("loginStatusMap") Map<Long, Integer> loginStatusMap,
            @Param("offset") long offset,
            @Param("pageSize") long pageSize);

    /**
     * 统计符合条件的用户总数
     * 
     * @param username 用户名（可选）
     * @return 用户总数
     */
    long countUsersByUsername(@Param("username") String username);
}
