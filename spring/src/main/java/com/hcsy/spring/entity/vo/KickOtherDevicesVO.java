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

    private Long userId;
    private Integer removedSessionCount;
    private Long onlineDeviceCount;
}
