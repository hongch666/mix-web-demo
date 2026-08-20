package com.hcsy.spring.common.utils;

import java.util.HashMap;
import java.util.Map;

import com.hcsy.spring.entity.po.Article;

/**
 * 实体转 Map 工具类，用于内部接口返回通用数据
 */
public final class EntityMapUtil {

    private EntityMapUtil() {
    }

    public static Map<String, Object> articleToMap(Article article) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", article.getId());
        map.put("title", article.getTitle());
        map.put("content", article.getContent());
        map.put("user_id", article.getUserId());
        map.put("tags", article.getTags());
        map.put("status", article.getStatus());
        map.put("views", article.getViews());
        map.put("sub_category_id", article.getSubCategoryId());
        map.put("create_at", article.getCreateAt());
        map.put("update_at", article.getUpdateAt());
        return map;
    }
}
