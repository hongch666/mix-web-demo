package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;

import lombok.Data;

@Data
@Schema(description = "分页结果")
public class PageDTO<T> implements Serializable {
    @Schema(description = "当前页码")
    private long current;

    @Schema(description = "每页条数")
    private long size;

    @Schema(description = "总记录数")
    private long total;

    @Schema(description = "当前页记录")
    private List<T> records;
}
