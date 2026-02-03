package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "用户查询参数")
public class UserQueryDTO {
    @Schema(description = "页码", example = "1")
    private int page = 1;

    @Schema(description = "每页条数", example = "10")
    private int size = 10;

    @Schema(description = "用户名（模糊匹配）", hidden = true)
    private String username;
}
