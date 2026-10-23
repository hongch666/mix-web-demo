package com.hcsy.spring;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;

import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.infra.client.ServiceWebClient;

/**
 * 应用上下文冒烟测试
 *
 * 依赖装配、属性绑定与条件装配错误只在容器启动时暴露，
 * 纯语法编译与 Mockito 单元测试都无法发现，此处通过加载完整上下文兜底。
 * 测试离线运行：Nacos 由 test/resources/bootstrap.yaml 关闭，
 * MySQL/Redis/RabbitMQ 均为惰性连接，启动失败只记日志不阻断上下文加载
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE, properties = {
    "management.server.port=0", // 避免与运行中的 9101 监控端口冲突
    "user.default-password=smoke-test", // UserPasswordProperties 的 @NotBlank 必填项
    "user.reset-password=smoke-test",
    // R2DBC 连接池在启动时实例化，凭据为空会直接失败；占位值即可，不会真实建连
    "spring.r2dbc.username=smoke-test",
    "spring.r2dbc.password=smoke-test",
    // InternalTokenUtil 初始化校验密钥非空且 HMAC-SHA256 要求至少 256 位（32 字节）；
    // 两个键都提供，覆盖 application.yaml 里 internal-token.secret=${INTERNAL_TOKEN_SECRET:} 的占位符解析
    "internal-token.secret=smoke-test-secret-0123456789abcdef",
    "INTERNAL_TOKEN_SECRET=smoke-test-secret-0123456789abcdef",
    // JwtUtil 初始化同样校验密钥非空与长度
    "jwt.secret=smoke-test-secret-0123456789abcdef",
    "JWT_SECRET=smoke-test-secret-0123456789abcdef",
})
class ApplicationTest {

    @Test
    void contextLoads(@Autowired ApplicationContext context) {
        // 关键基础设施 Bean 存在，说明依赖装配与属性绑定全部成功
        assertThat(context.getBean(SimpleLogger.class)).isNotNull();
        assertThat(context.getBean(ServiceWebClient.class)).isNotNull();
    }
}
