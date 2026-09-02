package com.hcsy.spring.infra.grpc;

import com.hcsy.spring.proto.common.v1.JsonRequest;
import com.hcsy.spring.proto.common.v1.Result;
import com.hcsy.spring.proto.user.v1.UserGrpc;
import io.grpc.stub.StreamObserver;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class SpringUserGrpcService extends UserGrpc.UserImplBase {
    private final SpringGrpcBridgeService bridge;
    public void get(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/users/0", HttpMethod.GET); }
    public void batch(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/users/batch", HttpMethod.POST); }
    public void byName(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/users/by-name", HttpMethod.GET); }
    public void byGithubId(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/users/by-github-id/0", HttpMethod.GET); }
    public void githubUser(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/users/github-user", HttpMethod.POST); }
    public void isAdmin(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/users/0/is-admin", HttpMethod.GET); }
    public void tokenTicket(JsonRequest r, StreamObserver<Result> o) { bridge.forward(r, o, "/users/github/token-ticket", HttpMethod.POST); }
}
