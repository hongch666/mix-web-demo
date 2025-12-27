package com.hcsy.spring.api.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.vo.FocusUserVO;

public interface FocusService extends IService<Focus> {

    /**
     * 新增关注
     */
    boolean addFocus(Long userId, Long focusId);

    /**
     * 取消关注
     */
    boolean removeFocus(Long userId, Long focusId);

    /**
     * 查询用户是否关注了某个用户
     */
    boolean isFocused(Long userId, Long focusId);

    /**
     * 查询用户的所有关注作者（分页）
     */
    IPage<FocusUserVO> listUserFocuses(Long userId, Page<Focus> page);

    /**
     * 查询用户的所有粉丝（分页）
     */
    IPage<FocusUserVO> listUserFollowers(Long userId, Page<Focus> page);

    /**
     * 获取用户的关注数
     */
    Long getFocusCountByUserId(Long userId);

    /**
     * 获取用户的粉丝数
     */
    Long getFollowerCountByUserId(Long userId);
}
