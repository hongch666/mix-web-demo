package com.hcsy.spring.application.service;

import java.util.List;

import com.hcsy.spring.entity.dto.CommentCreateDTO;
import com.hcsy.spring.entity.dto.CommentUpdateDTO;
import com.hcsy.spring.entity.dto.CommentsQueryDTO;
import com.hcsy.spring.entity.dto.PageDTO;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.vo.AICommentsVO;
import com.hcsy.spring.entity.vo.ArticleCommentScoresVO;
import com.hcsy.spring.entity.vo.CommentSyncVO;
import com.hcsy.spring.entity.vo.CommentsVO;
import com.hcsy.spring.entity.vo.MapDataVO;
import com.hcsy.spring.entity.vo.PageVO;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 评论业务接口，定义普通用户与AI评论的创建、更新、删除、分页条件查询、评论评分统计及Neo4j同步数据获取等响应式操作
 */
public interface CommentsService {
    /**
     * 根据文章标题与用户名解析关联ID后创建评论
     */
    Mono<Comments> createComment(CommentCreateDTO dto);

    /**
     * 根据文章标题与用户名校验后更新评论内容与评分
     */
    Mono<Comments> updateComment(CommentUpdateDTO dto);

    /**
     * 查询单条评论详情并补充用户与文章信息
     */
    Mono<CommentsVO> getCommentDetail(Long id);

    /**
     * 将评论分页结果批量补充用户名与文章标题
     */
    Mono<PageVO<CommentsVO>> listCommentDetails(PageDTO<Comments> page);

    /**
     * 查询文章的AI评论列表并补充AI用户名称与头像
     */
    Mono<List<AICommentsVO>> listAICommentDetailsByArticleId(Long articleId);

    /**
     * 按ID批量查询评论并转为Neo4j同步视图对象
     */
    Mono<List<CommentSyncVO>> getCommentSyncByIds(java.util.Collection<Long> ids);
    /**
     * 按用户名、文章标题、内容条件分页查询普通用户评论
     */
    Mono<PageDTO<Comments>> listCommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO);

    /**
     * 按条件分页查询AI用户评论
     */
    Mono<PageDTO<Comments>> listAICommentsWithFilter(long page, long size, CommentsQueryDTO queryDTO);

    /**
     * 分页查询指定用户发表的评论
     */
    Mono<PageDTO<Comments>> listCommentsByUserId(long page, long size, Long userId);

    /**
     * 分页查询文章下普通用户评论，支持按评分或时间排序
     */
    Mono<PageDTO<Comments>> listCommentsByArticleId(long page, long size, Long articleId, String sortWay);

    /**
     * 流式查询文章下所有AI用户评论
     */
    Flux<Comments> listAICommentsByArticleId(Long articleId);

    /**
     * 在事务中保存评论实体
     */
    Mono<Comments> save(Comments comments);

    /**
     * 在事务中更新评论，仅允许修改内容与评分防止越权
     */
    Mono<Comments> update(Comments comments);

    /**
     * 按ID查询单条评论
     */
    Mono<Comments> getById(Long id);

    /**
     * 批量查询评论，供内部服务按主键精确同步
     */
    Flux<Comments> listByIds(java.util.Collection<Long> ids);

    /**
     * 删除指定评论，评论不存在时抛出404异常
     */
    Mono<Void> deleteComment(Long id);

    /**
     * 批量删除评论，任一ID不存在时抛出404异常
     */
    Mono<Void> deleteComments(List<Long> ids);

    /**
     * 批量查询文章评论评分，按角色（ai/user）分组
     */
    Mono<List<ArticleCommentScoresVO>> getCommentScoresByArticleIds(
        java.util.Collection<Long> articleIds);

    /**
     * 获取文章的AI评论数
     */
    Mono<Long> getAiCommentsNumByArticleId(Long articleId);

    /**
     * 删除文章的AI评论
     */
    Mono<Void> deleteAiCommentsByArticleId(Long articleId);

    /**
     * 获取用户本月评论的趋势
     */
    Mono<MapDataVO> getMonthlyCommentTrend(Long userId);

    /**
     * 获取评论数据，用于Neo4j同步
     *
     * @param updatedAfter
     *                         增量同步时间（ISO格式），为空则全量
     */
    Mono<List<CommentSyncVO>> getNeo4jSyncComments(String updatedAfter);
}
