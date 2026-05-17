package com.hcsy.spring.entity.vo;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentTableSchemaVO {
    @JsonProperty("table_name")
    private String tableName;

    private List<AgentColumnVO> columns;

    @JsonProperty("primary_key")
    private List<String> primaryKey;

    private List<AgentIndexVO> indexes;
}
