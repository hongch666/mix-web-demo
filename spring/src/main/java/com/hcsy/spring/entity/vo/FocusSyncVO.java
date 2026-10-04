package com.hcsy.spring.entity.vo;

import java.time.LocalDateTime;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户关注关系同步数据视图对象
 * 用于「用户 - 用户」关注关系同步
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Schema(description = "用户关注关系同步数据")
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class FocusSyncVO {

    @Schema(description = "关注发起用户ID")
    private Long userId;

    @Schema(description = "被关注用户ID")
    private Long focusId;

    @Schema(description = "关注时间")
    private LocalDateTime createdTime;
}
