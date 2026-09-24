package com.hcsy.spring.entity.po;

import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Table("focus")
@Schema(description = "用户关注")
public class Focus {
    @Schema(description = "关注记录ID")
    @Id
    private Long id;

    @Schema(description = "发起关注的用户ID")
    private Long userId;

    @Schema(description = "被关注用户ID")
    private Long focusId;

    @Schema(description = "关注时间")
    private LocalDateTime createdTime;
}
