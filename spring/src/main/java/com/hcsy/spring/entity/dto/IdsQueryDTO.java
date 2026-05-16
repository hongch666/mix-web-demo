package com.hcsy.spring.entity.dto;

import java.util.List;

import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

@Data
public class IdsQueryDTO {
    @NotEmpty(message = "ID列表不能为空")
    private List<Long> ids;
}
