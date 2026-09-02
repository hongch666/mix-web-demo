package com.hcsy.spring.infra.grpc;

import com.hcsy.spring.common.utils.InternalTokenUtil;
import io.grpc.Context;
import io.grpc.Contexts;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import io.grpc.Status;
import io.grpc.ForwardingServerCallListener;
import io.grpc.ServerCall.Listener;
import org.springframework.stereotype.Component;

/** Applies the same internal-token boundary to gRPC as the HTTP controllers. */
@Component
public class SpringGrpcAuthInterceptor implements ServerInterceptor {
    private static final Metadata.Key<String> INTERNAL_TOKEN = Metadata.Key.of(
        "x-internal-token", Metadata.ASCII_STRING_MARSHALLER);
    private static final Metadata.Key<String> USER_ID = Metadata.Key.of(
        "x-user-id", Metadata.ASCII_STRING_MARSHALLER);
    private static final Context.Key<String> USER_ID_CONTEXT = Context.key("grpc-user-id");

    private final InternalTokenUtil internalTokenUtil;

    public SpringGrpcAuthInterceptor(InternalTokenUtil internalTokenUtil) {
        this.internalTokenUtil = internalTokenUtil;
    }

    @Override
    public <ReqT, RespT> Listener<ReqT> interceptCall(ServerCall<ReqT, RespT> call,
        Metadata headers, ServerCallHandler<ReqT, RespT> next) {
        String value = headers.get(INTERNAL_TOKEN);
        String token = value != null && value.startsWith("Bearer ") ? value.substring(7) : value;
        if (token == null || token.isBlank()) {
            call.close(Status.UNAUTHENTICATED.withDescription("内部服务令牌缺失"), new Metadata());
            return new Listener<>() {};
        }
        try {
            internalTokenUtil.validateInternalToken(token);
        } catch (RuntimeException error) {
            call.close(Status.UNAUTHENTICATED.withDescription("内部服务令牌无效"), new Metadata());
            return new Listener<>() {};
        }
        Context context = Context.current().withValue(USER_ID_CONTEXT, headers.get(USER_ID));
        Listener<ReqT> listener = Contexts.interceptCall(context, call, headers, next);
        return new ForwardingServerCallListener.SimpleForwardingServerCallListener<>(listener) {};
    }
}
