package com.hcsy.spring.entity.vo;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentSqlResultVO {
    private List<String> columns;
    private List<List<Object>> rows;

    @JsonProperty("total_rows")
    private Integer totalRows;
}
