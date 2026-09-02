package com.hcsy.nestjs.proto.email.v1;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.66.0)",
    comments = "Source: nestjs/email.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class EmailGrpc {

  private EmailGrpc() {}

  public static final java.lang.String SERVICE_NAME = "nestjs.v1.Email";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSendCodeMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "SendCode",
      requestType = com.hcsy.spring.proto.common.v1.JsonRequest.class,
      responseType = com.hcsy.spring.proto.common.v1.Result.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest,
      com.hcsy.spring.proto.common.v1.Result> getSendCodeMethod() {
    io.grpc.MethodDescriptor<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result> getSendCodeMethod;
    if ((getSendCodeMethod = EmailGrpc.getSendCodeMethod) == null) {
      synchronized (EmailGrpc.class) {
        if ((getSendCodeMethod = EmailGrpc.getSendCodeMethod) == null) {
          EmailGrpc.getSendCodeMethod = getSendCodeMethod =
              io.grpc.MethodDescriptor.<com.hcsy.spring.proto.common.v1.JsonRequest, com.hcsy.spring.proto.common.v1.Result>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "SendCode"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.JsonRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.hcsy.spring.proto.common.v1.Result.getDefaultInstance()))
              .setSchemaDescriptor(new EmailMethodDescriptorSupplier("SendCode"))
              .build();
        }
      }
    }
    return getSendCodeMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static EmailStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<EmailStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<EmailStub>() {
        @java.lang.Override
        public EmailStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new EmailStub(channel, callOptions);
        }
      };
    return EmailStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static EmailBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<EmailBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<EmailBlockingStub>() {
        @java.lang.Override
        public EmailBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new EmailBlockingStub(channel, callOptions);
        }
      };
    return EmailBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static EmailFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<EmailFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<EmailFutureStub>() {
        @java.lang.Override
        public EmailFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new EmailFutureStub(channel, callOptions);
        }
      };
    return EmailFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void sendCode(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getSendCodeMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service Email.
   */
  public static abstract class EmailImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return EmailGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service Email.
   */
  public static final class EmailStub
      extends io.grpc.stub.AbstractAsyncStub<EmailStub> {
    private EmailStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected EmailStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new EmailStub(channel, callOptions);
    }

    /**
     */
    public void sendCode(com.hcsy.spring.proto.common.v1.JsonRequest request,
        io.grpc.stub.StreamObserver<com.hcsy.spring.proto.common.v1.Result> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getSendCodeMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service Email.
   */
  public static final class EmailBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<EmailBlockingStub> {
    private EmailBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected EmailBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new EmailBlockingStub(channel, callOptions);
    }

    /**
     */
    public com.hcsy.spring.proto.common.v1.Result sendCode(com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getSendCodeMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service Email.
   */
  public static final class EmailFutureStub
      extends io.grpc.stub.AbstractFutureStub<EmailFutureStub> {
    private EmailFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected EmailFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new EmailFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<com.hcsy.spring.proto.common.v1.Result> sendCode(
        com.hcsy.spring.proto.common.v1.JsonRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getSendCodeMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_SEND_CODE = 0;

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
        case METHODID_SEND_CODE:
          serviceImpl.sendCode((com.hcsy.spring.proto.common.v1.JsonRequest) request,
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
          getSendCodeMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.hcsy.spring.proto.common.v1.JsonRequest,
              com.hcsy.spring.proto.common.v1.Result>(
                service, METHODID_SEND_CODE)))
        .build();
  }

  private static abstract class EmailBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    EmailBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.hcsy.nestjs.proto.email.v1.EmailOuterClass.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("Email");
    }
  }

  private static final class EmailFileDescriptorSupplier
      extends EmailBaseDescriptorSupplier {
    EmailFileDescriptorSupplier() {}
  }

  private static final class EmailMethodDescriptorSupplier
      extends EmailBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    EmailMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (EmailGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new EmailFileDescriptorSupplier())
              .addMethod(getSendCodeMethod())
              .build();
        }
      }
    }
    return result;
  }
}
