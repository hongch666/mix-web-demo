package com.hcsy.spring.entity.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ImageCaptchaVO {
    private String captchaId; // 图形验证码ID
    private String imageBase64; // 图形验证码base64
}
