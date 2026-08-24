package com.hcsy.spring.entity.vo;

import java.util.Map;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 通用 Map 数据视图对象，用于承载动态键值对的内部统计结果。
 * 使用具名字段持有 Map<String, Object>，避免 Result<T> 泛型擦除导致 Jackson 序列化失败。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class MapDataVO {
    private Map<String, Object> data;
}
