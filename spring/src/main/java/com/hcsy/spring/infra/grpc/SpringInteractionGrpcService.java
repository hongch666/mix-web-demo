package com.hcsy.spring.infra.grpc;

import com.hcsy.spring.proto.common.v1.JsonRequest;
import com.hcsy.spring.proto.common.v1.Result;
import com.hcsy.spring.proto.interaction.v1.InteractionGrpc;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class SpringInteractionGrpcService extends InteractionGrpc.InteractionImplBase {
    private final SpringGrpcBridgeService bridge;
    public void commentScores(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/comments/scores/batch", HttpMethod.POST); }
    public void likeCounts(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/likes/counts/batch", HttpMethod.POST); }
    public void collectCounts(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/collects/counts/batch", HttpMethod.POST); }
    public void followCounts(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/focus/counts/batch", HttpMethod.POST); }
    public void userLikes(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/likes/user/0", HttpMethod.GET); }
    public void userCollects(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/collects/user/0", HttpMethod.GET); }
    public void userFollowerCount(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/focus/count/follower/0", HttpMethod.GET); }
    public void commentsCreate(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/comments/internal/create", HttpMethod.POST); }
}
