package com.hcsy.spring.infra.grpc;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.proto.common.v1.JsonRequest;
import com.hcsy.spring.proto.common.v1.Result;
import java.util.Iterator;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

/** Shared HTTP bridge used by the Spring gRPC adapters. */
@Component
public class SpringGrpcBridgeService {
    private final WebClient.Builder webClientBuilder;
    private final ObjectMapper objectMapper;
    private final InternalTokenUtil internalTokenUtil;
    private final String httpHost;
    private final int httpPort;

    public SpringGrpcBridgeService(WebClient.Builder webClientBuilder, ObjectMapper objectMapper,
        InternalTokenUtil internalTokenUtil, @Value("${server.address:127.0.0.1}") String httpHost,
        @Value("${server.port:8081}") int httpPort) {
        this.webClientBuilder = webClientBuilder;
        this.objectMapper = objectMapper;
        this.internalTokenUtil = internalTokenUtil;
        this.httpHost = httpHost;
        this.httpPort = httpPort;
    }

    public void forward(JsonRequest request, io.grpc.stub.StreamObserver<Result> observer,
        String defaultPath, HttpMethod method) {
        try {
            JsonNode payload = parse(request);
            String requestedPath = payload.path("route").asText(
                payload.path("path").isTextual() ? payload.path("path").asText() : defaultPath);
            String path = requestedPath.startsWith("/") ? requestedPath : defaultPath;
            WebClient.RequestBodySpec requestSpec = webClientBuilder.build().method(method)
                .uri(uriBuilder -> {
                    var builder = uriBuilder.scheme("http").host(httpHost).port(httpPort).path(path);
                    JsonNode query = payload.path("query");
                    if (query.isObject()) {
                        Iterator<Map.Entry<String, JsonNode>> fields = query.fields();
                        while (fields.hasNext()) {
                            Map.Entry<String, JsonNode> field = fields.next();
                            if (!field.getValue().isNull()) builder.queryParam(field.getKey(), field.getValue().asText());
                        }
                    }
                    return builder.build();
                })
                .header("X-Internal-Token", "Bearer "
                    + internalTokenUtil.generateInternalToken(-1L, "spring-grpc"));
            Mono<JsonNode> response = payload.has("body") && !payload.get("body").isNull()
                ? requestSpec.bodyValue(payload.get("body")).retrieve().bodyToMono(JsonNode.class)
                : requestSpec.retrieve().bodyToMono(JsonNode.class);
            response.map(this::toGrpcResult).onErrorResume(error -> Mono.just(errorResult(error)))
                .subscribe(observer::onNext, observer::onError, observer::onCompleted);
        } catch (Exception error) {
            observer.onNext(errorResult(error));
            observer.onCompleted();
        }
    }

    private JsonNode parse(JsonRequest request) throws Exception {
        return request.getPayload().isEmpty() ? objectMapper.createObjectNode()
            : objectMapper.readTree(request.getPayload().toByteArray());
    }

    private Result toGrpcResult(JsonNode response) {
        return Result.newBuilder().setCode(response.path("code").asInt(500))
            .setMessage(response.path("msg").asText(response.path("message").asText("")))
            .setData(response.has("data") ? com.google.protobuf.ByteString.copyFrom(toJson(response.get("data")))
                : com.google.protobuf.ByteString.EMPTY).build();
    }

    private byte[] toJson(JsonNode data) {
        try { return objectMapper.writeValueAsBytes(data); } catch (Exception ignored) { return new byte[0]; }
    }

    private Result errorResult(Throwable error) {
        return Result.newBuilder().setCode(500)
            .setMessage(error.getMessage() == null ? "gRPC 请求处理失败" : error.getMessage()).build();
    }
}
