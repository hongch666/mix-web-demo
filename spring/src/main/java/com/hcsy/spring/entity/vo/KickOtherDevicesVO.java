package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KickOtherDevicesVO {

    private Long userId; // 用户ID
    private Integer removedTokenCount; // 被清除的 token 数量
    private Long onlineDeviceCount; // 剩余在线设备数
}
