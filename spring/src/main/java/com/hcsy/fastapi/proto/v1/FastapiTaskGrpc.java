package com.hcsy.fastapi.proto.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.66.0)",
    comments = "Source: fastapi/task.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class FastapiTaskGrpc {

  private FastapiTaskGrpc() {}

  public static final java.lang.String SERVICE_NAME = "fastapi.v1.FastapiTask";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSyncVectorMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "SyncVector",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSyncVectorMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getSyncVectorMethod;
    if ((getSyncVectorMethod = FastapiTaskGrpc.getSyncVectorMethod) == null) {
      synchronized (FastapiTaskGrpc.class) {
        if ((getSyncVectorMethod = FastapiTaskGrpc.getSyncVectorMethod) == null) {
          FastapiTaskGrpc.getSyncVectorMethod = getSyncVectorMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "SyncVector"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new FastapiTaskMethodDescriptorSupplier("SyncVector"))
              .build();
        }
      }
    }
    return getSyncVectorMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getClearAnalyzeCachesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ClearAnalyzeCaches",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getClearAnalyzeCachesMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getClearAnalyzeCachesMethod;
    if ((getClearAnalyzeCachesMethod = FastapiTaskGrpc.getClearAnalyzeCachesMethod) == null) {
      synchronized (FastapiTaskGrpc.class) {
        if ((getClearAnalyzeCachesMethod = FastapiTaskGrpc.getClearAnalyzeCachesMethod) == null) {
          FastapiTaskGrpc.getClearAnalyzeCachesMethod = getClearAnalyzeCachesMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ClearAnalyzeCaches"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new FastapiTaskMethodDescriptorSupplier("ClearAnalyzeCaches"))
              .build();
        }
      }
    }
    return getClearAnalyzeCachesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSyncNeo4jMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "SyncNeo4j",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSyncNeo4jMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getSyncNeo4jMethod;
    if ((getSyncNeo4jMethod = FastapiTaskGrpc.getSyncNeo4jMethod) == null) {
      synchronized (FastapiTaskGrpc.class) {
        if ((getSyncNeo4jMethod = FastapiTaskGrpc.getSyncNeo4jMethod) == null) {
          FastapiTaskGrpc.getSyncNeo4jMethod = getSyncNeo4jMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "SyncNeo4j"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new FastapiTaskMethodDescriptorSupplier("SyncNeo4j"))
              .build();
        }
      }
    }
    return getSyncNeo4jMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static FastapiTaskStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<FastapiTaskStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<FastapiTaskStub>() {
        @java.lang.Override
        public FastapiTaskStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new FastapiTaskStub(channel, callOptions);
        }
      };
    return FastapiTaskStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static FastapiTaskBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<FastapiTaskBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<FastapiTaskBlockingStub>() {
        @java.lang.Override
        public FastapiTaskBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new FastapiTaskBlockingStub(channel, callOptions);
        }
      };
    return FastapiTaskBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static FastapiTaskFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<FastapiTaskFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<FastapiTaskFutureStub>() {
        @java.lang.Override
        public FastapiTaskFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new FastapiTaskFutureStub(channel, callOptions);
        }
      };
    return FastapiTaskFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void syncVector(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getSyncVectorMethod(), responseObserver);
    }

    /**
     */
    default void clearAnalyzeCaches(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getClearAnalyzeCachesMethod(), responseObserver);
    }

    /**
     */
    default void syncNeo4j(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getSyncNeo4jMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service FastapiTask.
   */
  public static abstract class FastapiTaskImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return FastapiTaskGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service FastapiTask.
   */
  public static final class FastapiTaskStub
      extends io.grpc.stub.AbstractAsyncStub<FastapiTaskStub> {
    private FastapiTaskStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FastapiTaskStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new FastapiTaskStub(channel, callOptions);
    }

    /**
     */
    public void syncVector(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getSyncVectorMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void clearAnalyzeCaches(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getClearAnalyzeCachesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     */
    public void syncNeo4j(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getSyncNeo4jMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service FastapiTask.
   */
  public static final class FastapiTaskBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<FastapiTaskBlockingStub> {
    private FastapiTaskBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FastapiTaskBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new FastapiTaskBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result syncVector(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getSyncVectorMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result clearAnalyzeCaches(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getClearAnalyzeCachesMethod(), getCallOptions(), request);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result syncNeo4j(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getSyncNeo4jMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service FastapiTask.
   */
  public static final class FastapiTaskFutureStub
      extends io.grpc.stub.AbstractFutureStub<FastapiTaskFutureStub> {
    private FastapiTaskFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected FastapiTaskFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new FastapiTaskFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> syncVector(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getSyncVectorMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> clearAnalyzeCaches(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getClearAnalyzeCachesMethod(), getCallOptions()), request);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> syncNeo4j(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getSyncNeo4jMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_SYNC_VECTOR = 0;
  private static final int METHODID_CLEAR_ANALYZE_CACHES = 1;
  private static final int METHODID_SYNC_NEO4J = 2;

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
        case METHODID_SYNC_VECTOR:
          serviceImpl.syncVector((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_CLEAR_ANALYZE_CACHES:
          serviceImpl.clearAnalyzeCaches((com.hcsy.spring.proto.common.v1.JsonRequest) request,
              (io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result>) responseObserver);
          break;
        case METHODID_SYNC_NEO4J:
          serviceImpl.syncNeo4j((com.hcsy.spring.proto.common.v1.JsonRequest) request,
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
          getSyncVectorMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_SYNC_VECTOR)))
        .addMethod(
          getClearAnalyzeCachesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_CLEAR_ANALYZE_CACHES)))
        .addMethod(
          getSyncNeo4jMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_SYNC_NEO4J)))
        .build();
  }

  private static abstract class FastapiTaskBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    FastapiTaskBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.hcsy.fastapi.proto.v1.Task.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("FastapiTask");
    }
  }

  private static final class FastapiTaskFileDescriptorSupplier
      extends FastapiTaskBaseDescriptorSupplier {
    FastapiTaskFileDescriptorSupplier() {}
  }

  private static final class FastapiTaskMethodDescriptorSupplier
      extends FastapiTaskBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    FastapiTaskMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (FastapiTaskGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new FastapiTaskFileDescriptorSupplier())
              .addMethod(getSyncVectorMethod())
              .addMethod(getClearAnalyzeCachesMethod())
              .addMethod(getSyncNeo4jMethod())
              .build();
        }
      }
    }
    return result;
  }
}
