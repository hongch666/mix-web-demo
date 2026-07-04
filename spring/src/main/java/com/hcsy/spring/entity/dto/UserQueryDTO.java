package com.hcsy.spring.entity.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

@Data
@Schema(description = "用户查询参数")
public class UserQueryDTO {
    @Schema(description = "页码", example = "1")
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1;

    @Schema(description = "每页条数", example = "10")
    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 10;

    @Schema(description = "用户名（模糊匹配）", hidden = true)
    private String username;
}
