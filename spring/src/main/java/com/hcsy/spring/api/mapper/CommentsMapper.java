package com.hcsy.spring.api.mapper;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.hcsy.spring.entity.po.Comments;

@Mapper
public interface CommentsMapper extends BaseMapper<Comments> {

}
