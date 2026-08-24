package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * ID 与数量映射项，用于批量计数结果。
 * 使用具体元素类型承载，避免 Map<Long, Long> 泛型擦除导致 Jackson 序列化失败。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class IdCountVO {
    private Long id;
    private Long count;
}
