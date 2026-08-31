package com.hcsy.spring.common.constants;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Function;

import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;

/**
 * 数仓同步资源定义，不包含数据库 SQL
 */
public final class WarehouseResources {

    private WarehouseResources() {
    }

    public record ResourceSpec(
        Class<?> entityType,
        String watermarkProperty,
        Function<Object, LocalDateTime> watermarkGetter,
        Function<Object, Map<String, Object>> rowMapper) {
    }

    public static final Map<String, ResourceSpec> ALL = createResources();

    private static Map<String, ResourceSpec> createResources() {
        Map<String, ResourceSpec> resources = new LinkedHashMap<>();
        resources.put("articles", new ResourceSpec(Article.class, "updateAt",
            value -> ((Article) value).getUpdateAt(), value -> {
                Article article = (Article) value;
                return mapOf(
                    "id", article.getId(), "title", article.getTitle(), "user_id", article.getUserId(),
                    "sub_category_id", article.getSubCategoryId(), "tags", article.getTags(),
                    "status", defaultValue(article.getStatus(), 1), "views", defaultValue(article.getViews(), 0),
                    "create_at", article.getCreateAt(), "update_at", article.getUpdateAt());
            }));
        resources.put("user", new ResourceSpec(User.class, "updateAt",
            value -> ((User) value).getUpdateAt(), value -> {
                User user = (User) value;
                return mapOf(
                    "id", user.getId(), "name", user.getName(), "role", defaultValue(user.getRole(), "user"),
                    "img", defaultValue(user.getImg(), ""), "signature", defaultValue(user.getSignature(), ""),
                    "create_at", user.getCreateAt(), "update_at", user.getUpdateAt());
            }));
        resources.put("category", new ResourceSpec(Category.class, "updateTime",
            value -> ((Category) value).getUpdateTime(), value -> {
                Category category = (Category) value;
                return mapOf("id", category.getId(), "name", category.getName(),
                    "create_time", category.getCreateTime(), "update_time", category.getUpdateTime());
            }));
        resources.put("sub_category", new ResourceSpec(SubCategory.class, "updateTime",
            value -> ((SubCategory) value).getUpdateTime(), value -> {
                SubCategory category = (SubCategory) value;
                return mapOf("id", category.getId(), "name", category.getName(),
                    "category_id", category.getCategoryId(), "create_time", category.getCreateTime(),
                    "update_time", category.getUpdateTime());
            }));
        resources.put("likes", new ResourceSpec(ArticleLike.class, "createdTime",
            value -> ((ArticleLike) value).getCreatedTime(), value -> {
                ArticleLike like = (ArticleLike) value;
                return mapOf("id", like.getId(), "article_id", like.getArticleId(),
                    "user_id", like.getUserId(), "created_time", like.getCreatedTime());
            }));
        resources.put("collects", new ResourceSpec(ArticleCollect.class, "createdTime",
            value -> ((ArticleCollect) value).getCreatedTime(), value -> {
                ArticleCollect collect = (ArticleCollect) value;
                return mapOf("id", collect.getId(), "article_id", collect.getArticleId(),
                    "user_id", collect.getUserId(), "created_time", collect.getCreatedTime());
            }));
        resources.put("comments", new ResourceSpec(Comments.class, "updateTime",
            value -> ((Comments) value).getUpdateTime(), value -> {
                Comments comment = (Comments) value;
                return mapOf("id", comment.getId(), "user_id", comment.getUserId(),
                    "article_id", comment.getArticleId(), "star", defaultValue(comment.getStar(), 0D),
                    "create_time", comment.getCreateTime(), "update_time", comment.getUpdateTime());
            }));
        resources.put("focus", new ResourceSpec(Focus.class, "createdTime",
            value -> ((Focus) value).getCreatedTime(), value -> {
                Focus focus = (Focus) value;
                return mapOf("id", focus.getId(), "user_id", focus.getUserId(), "focus_id", focus.getFocusId(),
                    "created_time", focus.getCreatedTime());
            }));
        return Map.copyOf(resources);
    }

    private static Map<String, Object> mapOf(Object... values) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2) {
            result.put((String) values[index], values[index + 1]);
        }
        return result;
    }

    private static <T> T defaultValue(T value, T defaultValue) {
        return value == null ? defaultValue : value;
    }
}
