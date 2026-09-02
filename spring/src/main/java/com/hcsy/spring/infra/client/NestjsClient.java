package com.hcsy.spring.infra.client;

import org.springframework.http.HttpMethod;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.entity.dto.InternalEmailCodeSendDTO;

import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.Metadata;
import io.grpc.stub.MetadataUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.proto.common.v1.JsonRequest;
import com.hcsy.nestjs.proto.email.v1.EmailGrpc;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;

@Component
public class NestjsClient {
    private final ServiceWebClient serviceWebClient;
    private final InternalTokenUtil internalTokenUtil;
    private final ObjectMapper objectMapper;
    private final String grpcHost;
    private final int grpcPort;
    private ManagedChannel grpcChannel;

    public NestjsClient(ServiceWebClient serviceWebClient, InternalTokenUtil internalTokenUtil,
        ObjectMapper objectMapper, @Value("${services.nestjs.grpc-host:nestjs}") String grpcHost,
        @Value("${services.nestjs.grpc-port:9083}") int grpcPort) {
        this.serviceWebClient = serviceWebClient;
        this.internalTokenUtil = internalTokenUtil;
        this.objectMapper = objectMapper;
        this.grpcHost = grpcHost;
        this.grpcPort = grpcPort;
    }

    @PostConstruct
    void initGrpcChannel() {
        grpcChannel = ManagedChannelBuilder.forAddress(grpcHost, grpcPort).usePlaintext().build();
    }

    @PreDestroy
    void closeGrpcChannel() {
        if (grpcChannel != null) grpcChannel.shutdown();
    }

    public Mono<Result<?>> sendEmailCode(InternalEmailCodeSendDTO dto) {
        ServiceRequestOptions options = ServiceRequestOptions.builder()
            .body(dto)
            .build();
        return grpcEmailCode(dto).onErrorResume(error -> serviceWebClient.request(
            HttpMethod.POST, "nestjs", "/email/send-code", options,
            Messages.NESTJS_EMAIL_SERVICE_UNAVAILABLE_MSG));
    }

    private Mono<com.hcsy.spring.common.utils.Result<?>> grpcEmailCode(InternalEmailCodeSendDTO dto) {
        return Mono.defer(() -> {
            try {
                String token = internalTokenUtil.generateInternalToken(-1L, "spring");
                Metadata metadata = new Metadata();
                metadata.put(Metadata.Key.of("x-internal-token", Metadata.ASCII_STRING_MARSHALLER), "Bearer " + token);
                JsonRequest request = JsonRequest.newBuilder()
                    .setPayload(com.google.protobuf.ByteString.copyFrom(objectMapper.writeValueAsBytes(dto)))
                    .build();
                var future = EmailGrpc.newFutureStub(grpcChannel)
                    .withInterceptors(MetadataUtils.newAttachHeadersInterceptor(metadata))
                    .sendCode(request);
                return Mono.create(sink -> future.addListener(() -> {
                    try {
                        com.hcsy.spring.proto.common.v1.Result response = future.get();
                        if (response.getCode() != 200) sink.error(new IllegalStateException(response.getMessage()));
                        else sink.success(com.hcsy.spring.common.utils.Result.success(null));
                    } catch (Exception error) { sink.error(error); }
                }, Runnable::run));
            } catch (Exception error) {
                return Mono.error(error);
            }
        });
    }
}
