package com.hcsy.spring.entity.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "踢出其他设备结果")
public class KickOtherDevicesVO {
    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "已移除会话数")
    private Integer removedSessionCount;

    @Schema(description = "当前在线设备数")
    private Long onlineDeviceCount;
}
