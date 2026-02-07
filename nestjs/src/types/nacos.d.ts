declare module 'nacos' {
  class NacosNamingClient {
    constructor(options: any);
    ready(): Promise<void>;
    getAllInstances(serviceName: string): Promise<any[]>;
    registerInstance(serviceName: string, instance: any): Promise<void>;
  }

  export { NacosNamingClient };
}
