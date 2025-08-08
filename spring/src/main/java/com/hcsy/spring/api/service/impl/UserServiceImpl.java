package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;

import lombok.RequiredArgsConstructor;

import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.entity.po.User;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    private final UserMapper userMapper;
    private final RedisUtil redisUtil;

    @Override
    public IPage<User> listUsersWithFilter(Page<User> page, String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.like(User::getName, username); // 用户名模糊匹配
        }
        IPage<User> userPage = this.page(page, queryWrapper);

        // 为每个用户查redis登录状态，并设置到User对象
        List<User> userList = userPage.getRecords();
        for (User user : userList) {
            String status = (String) redisUtil.get("user:status:" + user.getId());
            // 建议在User类加一个transient Integer loginStatus字段
            user.setLoginStatus("1".equals(status) ? 1 : 0);
        }
        // 按loginStatus降序排序
        userList.sort((u1, u2) -> Integer.compare(u2.getLoginStatus(), u1.getLoginStatus()));

        // 重新设置排序后的列表
        userPage.setRecords(userList);
        return userPage;
    }

    @Transactional
    public void saveUserAndStatus(User user) {
        userMapper.insert(user);
        redisUtil.set("user:status:" + user.getId(), "0");
    }

    @Transactional
    public void deleteUserAndStatusById(Long id) {
        userMapper.deleteById(id);
        redisUtil.delete("user:status:" + id);
    }

    @Transactional
    public void deleteUsersAndStatusByIds(List<Long> ids) {
        if (ids == null || ids.isEmpty())
            return;
        userMapper.deleteBatchIds(ids);
        for (Long id : ids) {
            redisUtil.delete("user:status:" + id);
        }
    }

    @Transactional
    public User findByUsername(String username) {
        LambdaQueryWrapper<User> queryWrapper = Wrappers.lambdaQuery();
        if (username != null && !username.isEmpty()) {
            queryWrapper.eq(User::getName, username); // 用户名模糊匹配
        }
        return userMapper.selectOne(queryWrapper);
    }

}
