package com.hcsy.spring.infra.grpc;

import java.io.IOException;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/** Spring gRPC Server 生命周期管理。 */
@Component
@RequiredArgsConstructor
@Slf4j
public class SpringGrpcServer {
    private final SpringArticleGrpcService articleService;
    private final SpringCategoryGrpcService categoryService;
    private final SpringStatisticsGrpcService statisticsService;
    private final SpringUserGrpcService userService;
    private final SpringInteractionGrpcService interactionService;
    private final SpringGrpcAuthInterceptor authInterceptor;

    @Value("${grpc.server.enabled:true}")
    private boolean enabled;

    @Value("${grpc.server.port:9081}")
    private int port;

    private Server server;

    @PostConstruct
    public void start() throws IOException {
        if (!enabled) return;
        server = ServerBuilder.forPort(port)
            .intercept(authInterceptor)
            .addService(articleService)
            .addService(categoryService)
            .addService(statisticsService)
            .addService(userService)
            .addService(interactionService)
            .build()
            .start();
        log.info("Spring gRPC 服务已启动，监听端口: {}", port);
    }

    @PreDestroy
    public void stop() {
        if (server != null) {
            server.shutdown();
            log.info("Spring gRPC 服务已停止");
        }
    }
}
