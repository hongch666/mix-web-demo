package com.hcsy.spring.proto.article.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.66.0)",
    comments = "Source: spring/article.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class ArticleGrpc {

  private ArticleGrpc() {}

  public static final java.lang.String SERVICE_NAME = "spring.v1.Article";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getListMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "List",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getListMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getListMethod;
    if ((getListMethod = ArticleGrpc.getListMethod) == null) {
      synchronized (ArticleGrpc.class) {
        if ((getListMethod = ArticleGrpc.getListMethod) == null) {
          ArticleGrpc.getListMethod = getListMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "List"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new ArticleMethodDescriptorSupplier("List"))
              .build();
        }
      }
    }
    return getListMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getBatchMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Batch",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getBatchMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getBatchMethod;
    if ((getBatchMethod = ArticleGrpc.getBatchMethod) == null) {
      synchronized (ArticleGrpc.class) {
        if ((getBatchMethod = ArticleGrpc.getBatchMethod) == null) {
          ArticleGrpc.getBatchMethod = getBatchMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Batch"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new ArticleMethodDescriptorSupplier("Batch"))
              .build();
        }
      }
    }
    return getBatchMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getGetMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Get",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getGetMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getGetMethod;
    if ((getGetMethod = ArticleGrpc.getGetMethod) == null) {
      synchronized (ArticleGrpc.class) {
        if ((getGetMethod = ArticleGrpc.getGetMethod) == null) {
          ArticleGrpc.getGetMethod = getGetMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Get"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new ArticleMethodDescriptorSupplier("Get"))
              .build();
        }
      }
    }
    return getGetMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getByTitleMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ByTitle",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getByTitleMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getByTitleMethod;
    if ((getByTitleMethod = ArticleGrpc.getByTitleMethod) == null) {
      synchronized (ArticleGrpc.class) {
        if ((getByTitleMethod = ArticleGrpc.getByTitleMethod) == null) {
          ArticleGrpc.getByTitleMethod = getByTitleMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ByTitle"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new ArticleMethodDescriptorSupplier("ByTitle"))
              .build();
        }
      }
    }
    return getByTitleMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getViewsBatchMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ViewsBatch",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getViewsBatchMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getViewsBatchMethod;
    if ((getViewsBatchMethod = ArticleGrpc.getViewsBatchMethod) == null) {
      synchronized (ArticleGrpc.class) {
        if ((getViewsBatchMethod = ArticleGrpc.getViewsBatchMethod) == null) {
          ArticleGrpc.getViewsBatchMethod = getViewsBatchMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ViewsBatch"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new ArticleMethodDescriptorSupplier("ViewsBatch"))
              .build();
        }
      }
    }
    return getViewsBatchMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserArticlesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "UserArticles",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getUserArticlesMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getUserArticlesMethod;
    if ((getUserArticlesMethod = ArticleGrpc.getUserArticlesMethod) == null) {
      synchronized (ArticleGrpc.class) {
        if ((getUserArticlesMethod = ArticleGrpc.getUserArticlesMethod) == null) {
          ArticleGrpc.getUserArticlesMethod = getUserArticlesMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "UserArticles"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new ArticleMethodDescriptorSupplier("UserArticles"))
              .build();
        }
      }
    }
    return getUserArticlesMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static ArticleStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<ArticleStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<ArticleStub>() {
        @java.lang.Override
        public ArticleStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new ArticleStub(channel, callOptions);
        }
      };
    return ArticleStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static ArticleBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<ArticleBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<ArticleBlockingStub>() {
        @java.lang.Override
        public ArticleBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new ArticleBlockingStub(channel, callOptions);
        }
      };
    return ArticleBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static ArticleFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<ArticleFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<ArticleFutureStub>() {
        @java.lang.Override
        public ArticleFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new ArticleFutureStub(channel, callOptions);
        }
      };
    return ArticleFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void list(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getListMethod(), responseObserver);
    }

    /**
     */
    default void batch(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getBatchMethod(), responseObserver);
    }

    /**
     */
    default void get(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetMethod(), responseObserver);
    }

    /**
     */
    default void byTitle(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getByTitleMethod(), responseObserver);
    }

    /**
     */
    default void viewsBatch(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getViewsBatchMethod(), responseObserver);
    }

    /**
     */
    default void userArticles(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getUserArticlesMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service Article.
   */
  public static abstract class ArticleImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return ArticleGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service Article.
   */
  public static final class ArticleStub
      extends io.grpc.stub.AbstractAsyncStub<ArticleStub> {
    private ArticleStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected ArticleStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new ArticleStub(channel, callOptions);
    }

    /**
     */
    public void list(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getListMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void batch(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getBatchMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void get(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void byTitle(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getByTitleMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void viewsBatch(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getViewsBatchMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void userArticles(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getUserArticlesMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service Article.
   */
  public static final class ArticleBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<ArticleBlockingStub> {
    private ArticleBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected ArticleBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new ArticleBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result list(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getListMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result batch(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getBatchMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result get(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result byTitle(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getByTitleMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result viewsBatch(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getViewsBatchMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result userArticles(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getUserArticlesMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service Article.
   */
  public static final class ArticleFutureStub
      extends io.grpc.stub.AbstractFutureStub<ArticleFutureStub> {
    private ArticleFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected ArticleFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new ArticleFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> list(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getListMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> batch(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getBatchMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> get(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> byTitle(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getByTitleMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> viewsBatch(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getViewsBatchMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> userArticles(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getUserArticlesMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_LIST = 0;
  private static final int METHODID_BATCH = 1;
  private static final int METHODID_GET = 2;
  private static final int METHODID_BY_TITLE = 3;
  private static final int METHODID_VIEWS_BATCH = 4;
  private static final int METHODID_USER_ARTICLES = 5;

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
        case METHODID_LIST:
          serviceImpl.list((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_BATCH:
          serviceImpl.batch((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_GET:
          serviceImpl.get((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_BY_TITLE:
          serviceImpl.byTitle((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_VIEWS_BATCH:
          serviceImpl.viewsBatch((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_USER_ARTICLES:
          serviceImpl.userArticles((com.hcsy.spring.proto.common.v1.JsonRequest) request,
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
          getListMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_LIST)))
        .addMethod(
          getBatchMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_BATCH)))
        .addMethod(
          getGetMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_GET)))
        .addMethod(
          getByTitleMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_BY_TITLE)))
        .addMethod(
          getViewsBatchMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_VIEWS_BATCH)))
        .addMethod(
          getUserArticlesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_USER_ARTICLES)))
        .build();
  }

  private static abstract class ArticleBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    ArticleBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.hcsy.spring.proto.article.v1.ArticleOuterClass.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("Article");
    }
  }

  private static final class ArticleFileDescriptorSupplier
      extends ArticleBaseDescriptorSupplier {
    ArticleFileDescriptorSupplier() {}
  }

  private static final class ArticleMethodDescriptorSupplier
      extends ArticleBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    ArticleMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (ArticleGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new ArticleFileDescriptorSupplier())
              .addMethod(getListMethod())
              .addMethod(getBatchMethod())
              .addMethod(getGetMethod())
              .addMethod(getByTitleMethod())
              .addMethod(getViewsBatchMethod())
              .addMethod(getUserArticlesMethod())
              .build();
        }
      }
    }
    return result;
  }
}
