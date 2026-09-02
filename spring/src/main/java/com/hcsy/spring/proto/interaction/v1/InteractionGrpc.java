package com.hcsy.spring.proto.interaction.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.66.0)",
    comments = "Source: spring/interaction.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class InteractionGrpc {

  private InteractionGrpc() {}

  public static final java.lang.String SERVICE_NAME = "spring.v1.Interaction";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getCommentScoresMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CommentScores",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getCommentScoresMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getCommentScoresMethod;
    if ((getCommentScoresMethod = InteractionGrpc.getCommentScoresMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getCommentScoresMethod = InteractionGrpc.getCommentScoresMethod) == null) {
          InteractionGrpc.getCommentScoresMethod = getCommentScoresMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CommentScores"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("CommentScores"))
              .build();
        }
      }
    }
    return getCommentScoresMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getLikeCountsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "LikeCounts",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getLikeCountsMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getLikeCountsMethod;
    if ((getLikeCountsMethod = InteractionGrpc.getLikeCountsMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getLikeCountsMethod = InteractionGrpc.getLikeCountsMethod) == null) {
          InteractionGrpc.getLikeCountsMethod = getLikeCountsMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "LikeCounts"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("LikeCounts"))
              .build();
        }
      }
    }
    return getLikeCountsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getCollectCountsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CollectCounts",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getCollectCountsMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getCollectCountsMethod;
    if ((getCollectCountsMethod = InteractionGrpc.getCollectCountsMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getCollectCountsMethod = InteractionGrpc.getCollectCountsMethod) == null) {
          InteractionGrpc.getCollectCountsMethod = getCollectCountsMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CollectCounts"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("CollectCounts"))
              .build();
        }
      }
    }
    return getCollectCountsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getFollowCountsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "FollowCounts",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getFollowCountsMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getFollowCountsMethod;
    if ((getFollowCountsMethod = InteractionGrpc.getFollowCountsMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getFollowCountsMethod = InteractionGrpc.getFollowCountsMethod) == null) {
          InteractionGrpc.getFollowCountsMethod = getFollowCountsMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "FollowCounts"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("FollowCounts"))
              .build();
        }
      }
    }
    return getFollowCountsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserLikesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UserLikes",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserLikesMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getUserLikesMethod;
    if ((getUserLikesMethod = InteractionGrpc.getUserLikesMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getUserLikesMethod = InteractionGrpc.getUserLikesMethod) == null) {
          InteractionGrpc.getUserLikesMethod = getUserLikesMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UserLikes"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("UserLikes"))
              .build();
        }
      }
    }
    return getUserLikesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserCollectsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UserCollects",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserCollectsMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getUserCollectsMethod;
    if ((getUserCollectsMethod = InteractionGrpc.getUserCollectsMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getUserCollectsMethod = InteractionGrpc.getUserCollectsMethod) == null) {
          InteractionGrpc.getUserCollectsMethod = getUserCollectsMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UserCollects"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("UserCollects"))
              .build();
        }
      }
    }
    return getUserCollectsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserFollowerCountMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UserFollowerCount",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserFollowerCountMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getUserFollowerCountMethod;
    if ((getUserFollowerCountMethod = InteractionGrpc.getUserFollowerCountMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getUserFollowerCountMethod = InteractionGrpc.getUserFollowerCountMethod) == null) {
          InteractionGrpc.getUserFollowerCountMethod = getUserFollowerCountMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UserFollowerCount"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("UserFollowerCount"))
              .build();
        }
      }
    }
    return getUserFollowerCountMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getCommentsCreateMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CommentsCreate",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getCommentsCreateMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getCommentsCreateMethod;
    if ((getCommentsCreateMethod = InteractionGrpc.getCommentsCreateMethod) == null) {
      synchronized (InteractionGrpc.class) {
        if ((getCommentsCreateMethod = InteractionGrpc.getCommentsCreateMethod) == null) {
          InteractionGrpc.getCommentsCreateMethod = getCommentsCreateMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CommentsCreate"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new InteractionMethodDescriptorSupplier("CommentsCreate"))
              .build();
        }
      }
    }
    return getCommentsCreateMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static InteractionStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InteractionStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InteractionStub>() {
        @java.lang.Override
        public InteractionStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InteractionStub(channel, callOptions);
        }
      };
    return InteractionStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static InteractionBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InteractionBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InteractionBlockingStub>() {
        @java.lang.Override
        public InteractionBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InteractionBlockingStub(channel, callOptions);
        }
      };
    return InteractionBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static InteractionFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<InteractionFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<InteractionFutureStub>() {
        @java.lang.Override
        public InteractionFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new InteractionFutureStub(channel, callOptions);
        }
      };
    return InteractionFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void commentScores(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCommentScoresMethod(), responseObserver);
    }

    /**
     */
    default void likeCounts(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getLikeCountsMethod(), responseObserver);
    }

    /**
     */
    default void collectCounts(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCollectCountsMethod(), responseObserver);
    }

    /**
     */
    default void followCounts(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getFollowCountsMethod(), responseObserver);
    }

    /**
     */
    default void userLikes(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUserLikesMethod(), responseObserver);
    }

    /**
     */
    default void userCollects(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUserCollectsMethod(), responseObserver);
    }

    /**
     */
    default void userFollowerCount(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUserFollowerCountMethod(), responseObserver);
    }

    /**
     */
    default void commentsCreate(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getCommentsCreateMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service Interaction.
   */
  public static abstract class InteractionImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return InteractionGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service Interaction.
   */
  public static final class InteractionStub
      extends io.grpc.stub.AbstractAsyncStub<InteractionStub> {
    private InteractionStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InteractionStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InteractionStub(channel, callOptions);
    }

    /**
     */
    public void commentScores(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCommentScoresMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void likeCounts(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getLikeCountsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void collectCounts(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCollectCountsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void followCounts(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getFollowCountsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void userLikes(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUserLikesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void userCollects(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUserCollectsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void userFollowerCount(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUserFollowerCountMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void commentsCreate(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getCommentsCreateMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service Interaction.
   */
  public static final class InteractionBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<InteractionBlockingStub> {
    private InteractionBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InteractionBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InteractionBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result commentScores(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCommentScoresMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result likeCounts(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getLikeCountsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result collectCounts(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCollectCountsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result followCounts(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getFollowCountsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result userLikes(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUserLikesMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result userCollects(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUserCollectsMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result userFollowerCount(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUserFollowerCountMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result commentsCreate(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getCommentsCreateMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service Interaction.
   */
  public static final class InteractionFutureStub
      extends io.grpc.stub.AbstractFutureStub<InteractionFutureStub> {
    private InteractionFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected InteractionFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new InteractionFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> commentScores(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCommentScoresMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> likeCounts(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getLikeCountsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> collectCounts(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCollectCountsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> followCounts(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getFollowCountsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> userLikes(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUserLikesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> userCollects(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUserCollectsMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> userFollowerCount(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUserFollowerCountMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> commentsCreate(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getCommentsCreateMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_COMMENT_SCORES = 0;
  private static final int METHODID_LIKE_COUNTS = 1;
  private static final int METHODID_COLLECT_COUNTS = 2;
  private static final int METHODID_FOLLOW_COUNTS = 3;
  private static final int METHODID_USER_LIKES = 4;
  private static final int METHODID_USER_COLLECTS = 5;
  private static final int METHODID_USER_FOLLOWER_COUNT = 6;
  private static final int METHODID_COMMENTS_CREATE = 7;

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
        case METHODID_COMMENT_SCORES:
          serviceImpl.commentScores((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_LIKE_COUNTS:
          serviceImpl.likeCounts((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_COLLECT_COUNTS:
          serviceImpl.collectCounts((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_FOLLOW_COUNTS:
          serviceImpl.followCounts((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_USER_LIKES:
          serviceImpl.userLikes((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_USER_COLLECTS:
          serviceImpl.userCollects((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_USER_FOLLOWER_COUNT:
          serviceImpl.userFollowerCount((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_COMMENTS_CREATE:
          serviceImpl.commentsCreate((com.hcsy.spring.proto.common.v1.JsonRequest) request,
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
          getCommentScoresMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_COMMENT_SCORES)))
        .addMethod(
          getLikeCountsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_LIKE_COUNTS)))
        .addMethod(
          getCollectCountsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_COLLECT_COUNTS)))
        .addMethod(
          getFollowCountsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_FOLLOW_COUNTS)))
        .addMethod(
          getUserLikesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_USER_LIKES)))
        .addMethod(
          getUserCollectsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_USER_COLLECTS)))
        .addMethod(
          getUserFollowerCountMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_USER_FOLLOWER_COUNT)))
        .addMethod(
          getCommentsCreateMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_COMMENTS_CREATE)))
        .build();
  }

  private static abstract class InteractionBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    InteractionBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.hcsy.spring.proto.interaction.v1.InteractionOuterClass.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("Interaction");
    }
  }

  private static final class InteractionFileDescriptorSupplier
      extends InteractionBaseDescriptorSupplier {
    InteractionFileDescriptorSupplier() {}
  }

  private static final class InteractionMethodDescriptorSupplier
      extends InteractionBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    InteractionMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (InteractionGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new InteractionFileDescriptorSupplier())
              .addMethod(getCommentScoresMethod())
              .addMethod(getLikeCountsMethod())
              .addMethod(getCollectCountsMethod())
              .addMethod(getFollowCountsMethod())
              .addMethod(getUserLikesMethod())
              .addMethod(getUserCollectsMethod())
              .addMethod(getUserFollowerCountMethod())
              .addMethod(getCommentsCreateMethod())
              .build();
        }
      }
    }
    return result;
  }
}
