package com.hcsy.spring.entity.vo;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentColumnVO {
    private String name;
    private String type;
    private Boolean nullable;

    @JsonProperty("default")
    private String defaultValue;
}
