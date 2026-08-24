package com.hcsy.spring.entity.vo;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 批量计数视图对象，用于承载 ID 与数量的映射结果。
 * 使用 List<IdCountVO> 保存元素，避免 Map<Long, Long> 泛型擦除导致 Jackson 序列化失败。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class BatchCountVO {
    private List<IdCountVO> counts;
}
