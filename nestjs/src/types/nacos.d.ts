declare module "nacos" {
  export interface NacosInstance {
    ip: string;
    port: number | string;
    weight?: number;
    ephemeral?: boolean;
    clusterName?: string;
    serviceName?: string;
    enabled?: boolean;
    healthy?: boolean;
    metadata?: Record<string, string>;
  }

  class NacosNamingClient {
    constructor(options: Record<string, unknown>);
    ready(): Promise<void>;
    getAllInstances(serviceName: string): Promise<NacosInstance[]>;
    registerInstance(
      serviceName: string,
      instance: NacosInstance,
    ): Promise<void>;
  }

  export { NacosNamingClient };
}
