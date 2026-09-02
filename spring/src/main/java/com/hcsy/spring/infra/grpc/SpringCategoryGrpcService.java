package com.hcsy.spring.infra.grpc;

import com.hcsy.spring.proto.category.v1.CategoryGrpc;
import com.hcsy.spring.proto.common.v1.JsonRequest;
import com.hcsy.spring.proto.common.v1.Result;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class SpringCategoryGrpcService extends CategoryGrpc.CategoryImplBase {
    private final SpringGrpcBridgeService bridge;
    public void batch(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/category/batch", HttpMethod.POST); }
    public void subBatch(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/category/sub/batch", HttpMethod.POST); }
    public void all(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/category/internal/all", HttpMethod.GET); }
    public void subWithParent(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/category/internal/sub/with-parent", HttpMethod.GET); }
    public void referenceSub(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/category/reference/sub/0", HttpMethod.GET); }
}
