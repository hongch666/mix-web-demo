package com.hcsy.spring.infra.grpc;

import com.hcsy.spring.proto.common.v1.JsonRequest;
import com.hcsy.spring.proto.common.v1.Result;
import com.hcsy.spring.proto.statistics.v1.StatisticsGrpc;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class SpringStatisticsGrpcService extends StatisticsGrpc.StatisticsImplBase {
    private final SpringGrpcBridgeService bridge;
    public void article(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/statistics/total", HttpMethod.GET); }
    public void interaction(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/likes/statistics/total", HttpMethod.GET); }
    public void follow(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/focus/statistics/total-follows/0", HttpMethod.GET); }
    public void userPortrait(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/articles/user/0", HttpMethod.GET); }
}
