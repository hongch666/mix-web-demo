package com.hcsy.gozeroproto.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.66.0)",
    comments = "Source: gozero/task.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class GozeroTaskGrpc {

  private GozeroTaskGrpc() {}

  public static final java.lang.String SERVICE_NAME = "gozero.v1.GozeroTask";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSyncerMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Syncer",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSyncerMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getSyncerMethod;
    if ((getSyncerMethod = GozeroTaskGrpc.getSyncerMethod) == null) {
      synchronized (GozeroTaskGrpc.class) {
        if ((getSyncerMethod = GozeroTaskGrpc.getSyncerMethod) == null) {
          GozeroTaskGrpc.getSyncerMethod = getSyncerMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Syncer"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new GozeroTaskMethodDescriptorSupplier("Syncer"))
              .build();
        }
      }
    }
    return getSyncerMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static GozeroTaskStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<GozeroTaskStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<GozeroTaskStub>() {
        @java.lang.Override
        public GozeroTaskStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new GozeroTaskStub(channel, callOptions);
        }
      };
    return GozeroTaskStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static GozeroTaskBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<GozeroTaskBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<GozeroTaskBlockingStub>() {
        @java.lang.Override
        public GozeroTaskBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new GozeroTaskBlockingStub(channel, callOptions);
        }
      };
    return GozeroTaskBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static GozeroTaskFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<GozeroTaskFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<GozeroTaskFutureStub>() {
        @java.lang.Override
        public GozeroTaskFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new GozeroTaskFutureStub(channel, callOptions);
        }
      };
    return GozeroTaskFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void syncer(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getSyncerMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service GozeroTask.
   */
  public static abstract class GozeroTaskImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return GozeroTaskGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service GozeroTask.
   */
  public static final class GozeroTaskStub
      extends io.grpc.stub.AbstractAsyncStub<GozeroTaskStub> {
    private GozeroTaskStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected GozeroTaskStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new GozeroTaskStub(channel, callOptions);
    }

    /**
     */
    public void syncer(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getSyncerMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service GozeroTask.
   */
  public static final class GozeroTaskBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<GozeroTaskBlockingStub> {
    private GozeroTaskBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected GozeroTaskBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new GozeroTaskBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result syncer(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getSyncerMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service GozeroTask.
   */
  public static final class GozeroTaskFutureStub
      extends io.grpc.stub.AbstractFutureStub<GozeroTaskFutureStub> {
    private GozeroTaskFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected GozeroTaskFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new GozeroTaskFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> syncer(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getSyncerMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_SYNCER = 0;

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
        case METHODID_SYNCER:
          serviceImpl.syncer((com.hcsy.spring.proto.common.v1.JsonRequest) request,
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
          getSyncerMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_SYNCER)))
        .build();
  }

  private static abstract class GozeroTaskBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    GozeroTaskBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.hcsy.gozeroproto.v1.Task.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("GozeroTask");
    }
  }

  private static final class GozeroTaskFileDescriptorSupplier
      extends GozeroTaskBaseDescriptorSupplier {
    GozeroTaskFileDescriptorSupplier() {}
  }

  private static final class GozeroTaskMethodDescriptorSupplier
      extends GozeroTaskBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    GozeroTaskMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (GozeroTaskGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new GozeroTaskFileDescriptorSupplier())
              .addMethod(getSyncerMethod())
              .build();
        }
      }
    }
    return result;
  }
}
