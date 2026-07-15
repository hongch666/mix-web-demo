package com.hcsy.spring.api.service.impl;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.hcsy.spring.api.mapper.FocusMapper;
import com.hcsy.spring.api.mapper.UserMapper;
import com.hcsy.spring.api.service.FocusService;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.core.annotation.ArticleSync;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.FocusUserVO;

import cn.hutool.core.bean.BeanUtil;
import lombok.RequiredArgsConstructor;

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

    @SuppressWarnings("null")
    @Override
    @Transactional
    @ArticleSync(action = "unfocus", description = "取消关注了1个用户")
    public boolean removeFocus(Long userId, Long focusId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);
        queryWrapper.eq(Focus::getFocusId, focusId);

        return focusMapper.delete(queryWrapper) > 0;
    }

    @SuppressWarnings("null")
    @Override
    public boolean isFocused(Long userId, Long focusId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);
        queryWrapper.eq(Focus::getFocusId, focusId);

        return focusMapper.selectOne(queryWrapper) != null;
    }

    @SuppressWarnings("null")
    @Override
    public IPage<FocusUserVO> listUserFocuses(Long userId, Page<Focus> page) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);
        queryWrapper.orderByDesc(Focus::getCreatedTime);

        IPage<Focus> focusPage = this.page(page, queryWrapper);

        // 转换为VO，并关联用户信息
        List<FocusUserVO> voList = focusPage.getRecords().stream().map(
                focus -> {
                    User user = userMapper.selectById(focus.getFocusId());

                    if (user == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER).build();
                    }
                    FocusUserVO vo = BeanUtil.copyProperties(user, FocusUserVO.class);
                    vo.setFocusedTime(focus.getCreatedTime());

                    return vo;
                }).collect(Collectors.toList());

        // 构建新的分页结果
        Page<FocusUserVO> resultPage = new Page<>(page.getCurrent(), page.getSize(), focusPage.getTotal());
        resultPage.setRecords(voList);

        return resultPage;
    }

    @SuppressWarnings("null")
    @Override
    public IPage<FocusUserVO> listUserFollowers(Long userId, Page<Focus> page) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getFocusId, userId);
        queryWrapper.orderByDesc(Focus::getCreatedTime);

        IPage<Focus> focusPage = this.page(page, queryWrapper);

        // 转换为VO，并关联用户信息
        List<FocusUserVO> voList = focusPage.getRecords().stream().map(
                focus -> {
                    User user = userMapper.selectById(focus.getUserId());

                    if (user == null) {
                        throw BusinessException.builder().httpStatus(HttpCode.NOT_FOUND).errorMessage(Messages.UNDEFINED_USER).build();
                    }
                    FocusUserVO vo = BeanUtil.copyProperties(user, FocusUserVO.class);
                    vo.setFocusedTime(focus.getCreatedTime());

                    return vo;
                }).collect(Collectors.toList());

        // 构建新的分页结果
        Page<FocusUserVO> resultPage = new Page<>(page.getCurrent(), page.getSize(), focusPage.getTotal());
        resultPage.setRecords(voList);

        return resultPage;
    }

    @SuppressWarnings("null")
    @Override
    public Long getFocusCountByUserId(Long userId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getUserId, userId);

        return focusMapper.selectCount(queryWrapper);
    }

    @SuppressWarnings("null")
    @Override
    public Long getFollowerCountByUserId(Long userId) {
        LambdaQueryWrapper<Focus> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Focus::getFocusId, userId);

        return focusMapper.selectCount(queryWrapper);
    }
}
