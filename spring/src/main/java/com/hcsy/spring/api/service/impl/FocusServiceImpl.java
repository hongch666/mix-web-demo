package com.hcsy.spring.api.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.FocusMapper;
import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.FocusUserVO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hcsy.spring.common.annotation.ArticleSync;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class FocusServiceImpl extends ServiceImpl<FocusMapper, Focus> implements FocusService {

    private final FocusMapper focusMapper;
    private final UserMapper userMapper;

    @Override
    @Transactional
    @ArticleSync(action = "focus", description = "关注了1个用户")
    public boolean addFocus(Long userId, Long focusId) {
        // 检查是否已经关注
        if (isFocused(userId, focusId)) {
            return false;
        }

        Focus focus = new Focus();
        focus.setUserId(userId);
        focus.setFocusId(focusId);
        focus.setCreatedTime(LocalDateTime.now());

        return focusMapper.insert(focus) > 0;
    }

    @Override
    @Transactional
    @ArticleSync(action = "unfocus", description = "取消关注了1个用户")
    public boolean removeFocus(Long userId, Long focusId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);
        queryWrapper.eq(Focus::getFocusId, focusId);

        return focusMapper.delete(queryWrapper) > 0;
    }

    @Override
    @Transactional
    public boolean isFocused(Long userId, Long focusId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);
        queryWrapper.eq(Focus::getFocusId, focusId);

        return focusMapper.selectOne(queryWrapper) != null;
    }

    @Override
    @Transactional
    public IPage<FocusUserVO> listUserFocuses(Long userId, Page<Focus> page) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);
        queryWrapper.orderByDesc(Focus::getCreatedTime);

        IPage<Focus> focusPage = this.page(page, queryWrapper);

        // 转换为VO，并关联用户信息
        List<FocusUserVO> voList = focusPage.getRecords().stream().map(focus -> {
            User user = userMapper.selectById(focus.getFocusId());
            FocusUserVO vo = new FocusUserVO();

            if (user != null) {
                vo.setId(user.getId());
                vo.setName(user.getName());
                vo.setAge(user.getAge());
                vo.setEmail(user.getEmail());
                vo.setImg(user.getImg());
                vo.setSignature(user.getSignature());
                vo.setRole(user.getRole());
                vo.setFocusedTime(focus.getCreatedTime());
            }

            return vo;
        }).collect(Collectors.toList());

        // 构建新的分页结果
        Page<FocusUserVO> resultPage = new Page<>(page.getCurrent(), page.getSize(), focusPage.getTotal());
        resultPage.setRecords(voList);

        return resultPage;
    }

    @Override
    @Transactional
    public IPage<FocusUserVO> listUserFollowers(Long userId, Page<Focus> page) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getFocusId, userId);
        queryWrapper.orderByDesc(Focus::getCreatedTime);

        IPage<Focus> focusPage = this.page(page, queryWrapper);

        // 转换为VO，并关联用户信息
        List<FocusUserVO> voList = focusPage.getRecords().stream().map(focus -> {
            User user = userMapper.selectById(focus.getUserId());
            FocusUserVO vo = new FocusUserVO();

            if (user != null) {
                vo.setId(user.getId());
                vo.setName(user.getName());
                vo.setAge(user.getAge());
                vo.setEmail(user.getEmail());
                vo.setImg(user.getImg());
                vo.setSignature(user.getSignature());
                vo.setRole(user.getRole());
                vo.setFocusedTime(focus.getCreatedTime());
            }

            return vo;
        }).collect(Collectors.toList());

        // 构建新的分页结果
        Page<FocusUserVO> resultPage = new Page<>(page.getCurrent(), page.getSize(), focusPage.getTotal());
        resultPage.setRecords(voList);

        return resultPage;
    }

    @Override
    @Transactional
    public Long getFocusCountByUserId(Long userId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);

        return focusMapper.selectCount(queryWrapper);
    }

    @Override
    @Transactional
    public Long getFollowerCountByUserId(Long userId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getFocusId, userId);

        return focusMapper.selectCount(queryWrapper);
    }
}
