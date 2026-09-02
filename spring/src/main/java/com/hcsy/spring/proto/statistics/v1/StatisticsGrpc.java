package com.hcsy.spring.proto.statistics.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.66.0)",
    comments = "Source: spring/statistics.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class StatisticsGrpc {

  private StatisticsGrpc() {}

  public static final java.lang.String SERVICE_NAME = "spring.v1.Statistics";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getArticleMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Article",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getArticleMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getArticleMethod;
    if ((getArticleMethod = StatisticsGrpc.getArticleMethod) == null) {
      synchronized (StatisticsGrpc.class) {
        if ((getArticleMethod = StatisticsGrpc.getArticleMethod) == null) {
          StatisticsGrpc.getArticleMethod = getArticleMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Article"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new StatisticsMethodDescriptorSupplier("Article"))
              .build();
        }
      }
    }
    return getArticleMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getInteractionMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Interaction",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getInteractionMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getInteractionMethod;
    if ((getInteractionMethod = StatisticsGrpc.getInteractionMethod) == null) {
      synchronized (StatisticsGrpc.class) {
        if ((getInteractionMethod = StatisticsGrpc.getInteractionMethod) == null) {
          StatisticsGrpc.getInteractionMethod = getInteractionMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Interaction"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new StatisticsMethodDescriptorSupplier("Interaction"))
              .build();
        }
      }
    }
    return getInteractionMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getFollowMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Follow",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getFollowMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getFollowMethod;
    if ((getFollowMethod = StatisticsGrpc.getFollowMethod) == null) {
      synchronized (StatisticsGrpc.class) {
        if ((getFollowMethod = StatisticsGrpc.getFollowMethod) == null) {
          StatisticsGrpc.getFollowMethod = getFollowMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Follow"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new StatisticsMethodDescriptorSupplier("Follow"))
              .build();
        }
      }
    }
    return getFollowMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserPortraitMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UserPortrait",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserPortraitMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getUserPortraitMethod;
    if ((getUserPortraitMethod = StatisticsGrpc.getUserPortraitMethod) == null) {
      synchronized (StatisticsGrpc.class) {
        if ((getUserPortraitMethod = StatisticsGrpc.getUserPortraitMethod) == null) {
          StatisticsGrpc.getUserPortraitMethod = getUserPortraitMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UserPortrait"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new StatisticsMethodDescriptorSupplier("UserPortrait"))
              .build();
        }
      }
    }
    return getUserPortraitMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static StatisticsStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<StatisticsStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<StatisticsStub>() {
        @java.lang.Override
        public StatisticsStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new StatisticsStub(channel, callOptions);
        }
      };
    return StatisticsStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static StatisticsBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<StatisticsBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<StatisticsBlockingStub>() {
        @java.lang.Override
        public StatisticsBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new StatisticsBlockingStub(channel, callOptions);
        }
      };
    return StatisticsBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static StatisticsFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<StatisticsFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<StatisticsFutureStub>() {
        @java.lang.Override
        public StatisticsFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new StatisticsFutureStub(channel, callOptions);
        }
      };
    return StatisticsFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void article(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getArticleMethod(), responseObserver);
    }

    /**
     */
    default void interaction(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getInteractionMethod(), responseObserver);
    }

    /**
     */
    default void follow(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getFollowMethod(), responseObserver);
    }

    /**
     */
    default void userPortrait(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUserPortraitMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service Statistics.
   */
  public static abstract class StatisticsImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return StatisticsGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service Statistics.
   */
  public static final class StatisticsStub
      extends io.grpc.stub.AbstractAsyncStub<StatisticsStub> {
    private StatisticsStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected StatisticsStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new StatisticsStub(channel, callOptions);
    }

    /**
     */
    public void article(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getArticleMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void interaction(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getInteractionMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void follow(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getFollowMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void userPortrait(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUserPortraitMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service Statistics.
   */
  public static final class StatisticsBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<StatisticsBlockingStub> {
    private StatisticsBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected StatisticsBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new StatisticsBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result article(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getArticleMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result interaction(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getInteractionMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result follow(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getFollowMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result userPortrait(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUserPortraitMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service Statistics.
   */
  public static final class StatisticsFutureStub
      extends io.grpc.stub.AbstractFutureStub<StatisticsFutureStub> {
    private StatisticsFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected StatisticsFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new StatisticsFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> article(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getArticleMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> interaction(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getInteractionMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> follow(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getFollowMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> userPortrait(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUserPortraitMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_ARTICLE = 0;
  private static final int METHODID_INTERACTION = 1;
  private static final int METHODID_FOLLOW = 2;
  private static final int METHODID_USER_PORTRAIT = 3;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_ARTICLE:
          serviceImpl.article((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_INTERACTION:
          serviceImpl.interaction((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_FOLLOW:
          serviceImpl.follow((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_USER_PORTRAIT:
          serviceImpl.userPortrait((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getArticleMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_ARTICLE)))
        .addMethod(
          getInteractionMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_INTERACTION)))
        .addMethod(
          getFollowMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_FOLLOW)))
        .addMethod(
          getUserPortraitMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_USER_PORTRAIT)))
        .build();
  }

  private static abstract class StatisticsBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    StatisticsBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.hcsy.spring.proto.statistics.v1.StatisticsOuterClass.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("Statistics");
    }
  }

  private static final class StatisticsFileDescriptorSupplier
      extends StatisticsBaseDescriptorSupplier {
    StatisticsFileDescriptorSupplier() {}
  }

  private static final class StatisticsMethodDescriptorSupplier
      extends StatisticsBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    StatisticsMethodDescriptorSupplier(java.lang.String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (StatisticsGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new StatisticsFileDescriptorSupplier())
              .addMethod(getArticleMethod())
              .addMethod(getInteractionMethod())
              .addMethod(getFollowMethod())
              .addMethod(getUserPortraitMethod())
              .build();
        }
      }
    }
    return result;
  }
}
