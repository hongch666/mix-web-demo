package com.hcsy.spring.api.service.impl;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.scheduling.annotation.Async;
import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.Constants;
import com.hcsy.spring.common.utils.RedisUtil;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import java.util.Random;
import lombok.RequiredArgsConstructor;
import org.springframework.transaction.annotation.Transactional;

/**
 * 邮箱验证服务实现
 * 支持 QQ 邮箱、Gmail 等多种邮箱服务
 */
@Service
@RequiredArgsConstructor
@Transactional
public class EmailVerificationServiceImpl implements EmailVerificationService {

    private final JavaMailSender mailSender;
    private final RedisUtil redisUtil;
    private final SimpleLogger logger;

    @Value("${spring.mail.username}")
    private String mailFrom;

    private static final String VERIFICATION_CODE_PREFIX = "email:verify:";
    private static final long VERIFICATION_CODE_EXPIRY = 10 * 60; // 10分钟过期（秒）

    /**
     * 生成验证码（6位数字）
     */
    private String generateVerificationCode() {
        Random random = new Random();
        return String.format("%06d", random.nextInt(1000000));
    }

    /**
     * 发送邮箱验证码
     * 
     * @param email 目标邮箱
     * @return 是否发送成功
     */
    @Override
    public void sendVerificationCode(String email) {
        // 生成验证码
        String code = generateVerificationCode();

        // 保存到 Redis（设置过期时间）
        String key = VERIFICATION_CODE_PREFIX + email;
        redisUtil.set(key, code, VERIFICATION_CODE_EXPIRY);
        logger.info(Constants.CODE_SAVE + email + ": " + code);

        // 异步发送邮件，避免阻塞主线程
        sendEmailAsync(email, code);
    }

    /**
     * 异步发送邮件
     */
    @Async("taskExecutor")
    private void sendEmailAsync(String email, String code) {
        try {
            // 创建 MimeMessage
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            // 设置邮件信息
            helper.setFrom(mailFrom);
            helper.setTo(email);
            helper.setSubject(Constants.EMAIL_CODE);

            // 构建 HTML 邮件内容
            String htmlContent = buildEmailContent(code);
            helper.setText(htmlContent, true);

            // 发送邮件
            mailSender.send(message);
            logger.info(Constants.CODE_SUCCESS + email);
        } catch (MessagingException e) {
            logger.error(Constants.CODE_FAIL + e.getMessage(), e);
            handleSendFailure(email);
        } catch (Exception e) {
            logger.error(Constants.CODE_EXCEPTION + e.getMessage(), e);
            handleSendFailure(email);
        }
    }

    /**
     * 处理发送失败
     */
    private void handleSendFailure(String email) {
        String key = VERIFICATION_CODE_PREFIX + email;
        redisUtil.delete(key);
        logger.debug(Constants.CODE_DELETE + email);
    }

    /**
     * 构建邮件内容
     */
    private String buildEmailContent(String code) {
        return "<html><body style='font-family: Arial, sans-serif; background-color: #f9f9f9;'>" +
                "<div style='max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>"
                +
                "<div style='text-align: center; padding-bottom: 20px; border-bottom: 2px solid #ff6600;'>" +
                "<h2 style='color: #333; margin: 0;'>邮箱验证码</h2>" +
                "</div>" +
                "<div style='padding: 30px 0;'>" +
                "<p style='color: #666; font-size: 14px; line-height: 1.6;'>尊敬的用户，感谢您的使用！</p>" +
                "<p style='color: #666; font-size: 14px; line-height: 1.6; margin-top: 15px;'>您的邮箱验证码是：</p>" +
                "<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;'>"
                +
                "<strong style='font-size: 32px; color: white; letter-spacing: 3px; font-family: monospace;'>" + code
                + "</strong>" +
                "</div>" +
                "<p style='color: #999; font-size: 12px; line-height: 1.6;'>⏰ 验证码有效期为 <strong>10 分钟</strong>，请勿泄露给他人。</p>"
                +
                "<p style='color: #999; font-size: 12px; line-height: 1.6;'>❌ 如果不是您本人操作，请忽略此邮件。</p>" +
                "</div>" +
                "<hr style='border: none; border-top: 1px solid #eee; margin: 20px 0;'>" +
                "<p style='color: #bbb; font-size: 11px; text-align: center; line-height: 1.6;'>此邮件由系统自动发送，请勿直接回复。</p>"
                +
                "<p style='color: #bbb; font-size: 11px; text-align: center; line-height: 1.6;'>发送时间: "
                + java.time.LocalDateTime.now()
                        .format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
                + "</p>" +
                "</div>" +
                "</body></html>";
    }

    /**
     * 验证邮箱验证码
     * 
     * @param email 邮箱地址
     * @param code  验证码
     * @return 是否验证成功
     */
    @Override
    public boolean verifyCode(String email, String code) {
        try {
            String key = VERIFICATION_CODE_PREFIX + email;
            String storedCode = redisUtil.get(key);

            if (storedCode == null) {
                logger.info(Constants.CODE_EXPIRED + email);
                return false;
            }

            if (!storedCode.equals(code)) {
                logger.info(Constants.CODE_VERIFY_FAIL + email);
                return false;
            }

            // 验证成功，删除验证码
            redisUtil.delete(key);
            logger.info(Constants.CODE_VERIFY_SUCCESS + email);
            return true;
        } catch (Exception e) {
            logger.error(Constants.CODE_VERIFY_EXCEPTION + e.getMessage(), e);
            return false;
        }
    }

    /**
     * 检查邮箱验证状态
     * 
     * @param email 邮箱地址
     * @return 是否已验证
     */
    @Override
    public boolean isEmailVerified(String email) {
        String key = VERIFICATION_CODE_PREFIX + "verified:" + email;
        return redisUtil.get(key) != null;
    }

    /**
     * 标记邮箱已验证
     * 
     * @param email 邮箱地址
     */
    @Override
    public void markEmailAsVerified(String email) {
        String key = VERIFICATION_CODE_PREFIX + "verified:" + email;
        redisUtil.set(key, "true", 24 * 60 * 60); // 24小时
    }
}
