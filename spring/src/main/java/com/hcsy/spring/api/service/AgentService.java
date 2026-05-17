package com.hcsy.spring.api.service;

import java.util.List;

import com.hcsy.spring.entity.dto.AgentSqlQueryDTO;
import com.hcsy.spring.entity.vo.AgentSqlResultVO;
import com.hcsy.spring.entity.vo.AgentTableSchemaVO;

public interface AgentService {
    List<AgentTableSchemaVO> listTableSchemas(String name);

    AgentSqlResultVO query(AgentSqlQueryDTO dto);
}
