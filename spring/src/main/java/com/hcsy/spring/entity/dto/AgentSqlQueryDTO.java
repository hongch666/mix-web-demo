package com.hcsy.spring.entity.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.hcsy.spring.common.utils.Constants;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class AgentSqlQueryDTO {
    @NotBlank(message = Constants.AGENT_SQL_REQUIRED)
    private String sql;

    @JsonProperty("user_id")
    private Long userId;
}
