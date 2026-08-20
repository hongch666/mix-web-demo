package com.hcsy.spring.common.utils;

import java.util.LinkedHashMap;
import java.util.Map;

import com.hcsy.spring.entity.po.Article;
import com.hcsy.spring.entity.po.ArticleCollect;
import com.hcsy.spring.entity.po.ArticleLike;
import com.hcsy.spring.entity.po.Category;
import com.hcsy.spring.entity.po.Comments;
import com.hcsy.spring.entity.po.Focus;
import com.hcsy.spring.entity.po.SubCategory;
import com.hcsy.spring.entity.po.User;

/**
 * Neo4j同步数据转换工具，将实体PO转为Map，字段名与数据库列名保持一致。
 */
public final class Neo4jSyncMapUtil {

    private Neo4jSyncMapUtil() {
    }

    public static Map<String, Object> userToMap(User user) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", user.getId());
        map.put("name", user.getName());
        map.put("email", user.getEmail());
        map.put("role", user.getRole());
        map.put("img", user.getImg());
        map.put("signature", user.getSignature());
        map.put("created_at", user.getCreateAt());
        map.put("updated_at", user.getUpdateAt());
        return map;
    }

    public static Map<String, Object> categoryToMap(Category category) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", category.getId());
        map.put("name", category.getName());
        map.put("update_time", category.getUpdateTime());
        return map;
    }

    public static Map<String, Object> subCategoryToMap(SubCategory subCategory) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", subCategory.getId());
        map.put("name", subCategory.getName());
        map.put("category_id", subCategory.getCategoryId());
        map.put("update_time", subCategory.getUpdateTime());
        return map;
    }

    public static Map<String, Object> articleToMap(Article article) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", article.getId());
        map.put("title", article.getTitle());
        map.put("tags", article.getTags());
        map.put("status", article.getStatus());
        map.put("views", article.getViews());
        map.put("user_id", article.getUserId());
        map.put("sub_category_id", article.getSubCategoryId());
        map.put("create_at", article.getCreateAt());
        map.put("update_at", article.getUpdateAt());
        map.put("content", article.getContent());
        return map;
    }

    public static Map<String, Object> likeToMap(ArticleLike like) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("user_id", like.getUserId());
        map.put("article_id", like.getArticleId());
        map.put("created_time", like.getCreatedTime());
        return map;
    }

    public static Map<String, Object> collectToMap(ArticleCollect collect) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("user_id", collect.getUserId());
        map.put("article_id", collect.getArticleId());
        map.put("created_time", collect.getCreatedTime());
        return map;
    }

    public static Map<String, Object> commentToMap(Comments comment) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", comment.getId());
        map.put("user_id", comment.getUserId());
        map.put("article_id", comment.getArticleId());
        map.put("create_time", comment.getCreateTime());
        map.put("update_time", comment.getUpdateTime());
        return map;
    }

    public static Map<String, Object> focusToMap(Focus focus) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("user_id", focus.getUserId());
        map.put("focus_id", focus.getFocusId());
        map.put("created_time", focus.getCreatedTime());
        return map;
    }
}
