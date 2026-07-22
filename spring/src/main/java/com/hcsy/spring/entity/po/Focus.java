package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import lombok.Data;

@Data
@Table("focus")
public class Focus {
    @Id
    private Long id;
    private Long userId;
    private Long focusId;
    private LocalDateTime createdTime;
}
