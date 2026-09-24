package com.hcsy.spring.entity.vo;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "分页结果")
public class PageVO<T> {
    @Schema(description = "总记录数")
    private Long total;

    @Schema(description = "当前页数据")
    private List<T> list;
}
