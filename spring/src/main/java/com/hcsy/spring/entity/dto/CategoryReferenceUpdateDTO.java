package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 更新子分类权威参考文本的请求，字段与创建请求一致
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Schema(description = "更新权威参考文本请求")
public class CategoryReferenceUpdateDTO extends CategoryReferenceCreateDTO {

}
