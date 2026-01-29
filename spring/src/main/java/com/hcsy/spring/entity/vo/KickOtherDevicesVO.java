package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 踢出其他设备返回对象
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KickOtherDevicesVO {
    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 被清除的 token 数量
     */
    private Integer removedTokenCount;

    /**
     * 剩余在线设备数
     */
    private Long onlineDeviceCount;
}
