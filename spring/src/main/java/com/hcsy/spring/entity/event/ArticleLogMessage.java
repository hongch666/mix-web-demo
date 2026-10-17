package com.hcsy.spring.entity.event;

import java.util.List;

import com.hcsy.spring.common.constants.SyncAction;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Builder;
import lombok.Data;

/**
 * 文章日志消息
 * 由 ArticleSyncAspect 构建后投递到 article-log-queue，字段名与 NestJS 消费者约定保持一致
 */
@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ArticleLogMessage {

    /** 操作类型，序列化为注解约定的字符串值 */
    private SyncAction action;

    /** 资源名，见 SyncResource */
    private String resource;

    /** 变更类型，见 SyncChangeType */
    private String changeType;

    /** 操作描述 */
    private String msg;

    /** 触发操作的用户 ID */
    private Long userId;

    /** 单个文章 ID，关注类操作以 -1 占位 */
    private Long articleId;

    /** 批量操作涉及的文章 ID */
    private List<Long> articleIds;

    /** 操作内容明细，字段随操作类型变化 */
    private Content content;

    /**
     * 操作内容明细
     * 未使用的字段不参与序列化，保持与原有消息结构一致
     */
    @Data
    @Builder
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class Content {

        /** 单个资源 ID */
        private Long id;

        /** 批量资源 ID */
        private List<Long> ids;

        /** 文章标题 */
        private String title;

        /** 文章标签 */
        private String tags;

        /** 关注关系中的发起用户 */
        private Long sourceUserId;

        /** 关注关系中的目标用户 */
        private Long targetUserId;
    }
}
