package com.hcsy.spring.infra.grpc;

import com.hcsy.spring.proto.article.v1.ArticleGrpc;
import com.hcsy.spring.proto.common.v1.JsonRequest;
import com.hcsy.spring.proto.common.v1.Result;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class SpringArticleGrpcService extends ArticleGrpc.ArticleImplBase {
    private final SpringGrpcBridgeService bridge;
    public void list(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/list", HttpMethod.GET); }
    public void batch(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/batch", HttpMethod.POST); }
    public void get(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/0", HttpMethod.GET); }
    public void byTitle(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/by-title", HttpMethod.GET); }
    public void viewsBatch(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/views/batch", HttpMethod.POST); }
    public void userArticles(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/user/0", HttpMethod.GET); }
}
