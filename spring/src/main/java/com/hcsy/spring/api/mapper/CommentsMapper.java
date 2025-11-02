package com.hcsy.spring.api.mapper;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.hcsy.spring.entity.po.Comments;

@Mapper
public interface CommentsMapper extends BaseMapper<Comments> {
        /**
         * 获取文章评论（已过滤AI用户），使用SQL级别JOIN，确保分页基于过滤后的数据
         */
        IPage<Comments> selectCommentsByArticleIdWithoutAI(Page<Comments> page, @Param("articleId") Long articleId,
                        @Param("sortWay") String sortWay);

        /**
         * 获取文章评论（普通用户在前，AI用户在后）
         * 通过JOIN user表，根据role字段排序
         */
        IPage<Comments> selectCommentsWithFilter(Page<Comments> page,
                        @Param("content") String content,
                        @Param("articleIds") List<Long> articleIds,
                        @Param("userIds") List<Long> userIds);
}
