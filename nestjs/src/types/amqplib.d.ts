declare module 'amqplib' {
  import * as amqp from 'amqplib';

  export = amqp;
  export as namespace amqp;
}