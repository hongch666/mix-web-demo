import { Injectable } from "@nestjs/common";
import { NacosService } from "../nacos/nacos.service";

@Injectable()
export class SpringClientService {
  constructor(private readonly nacosService: NacosService) {}

  async createTokenTicket(
    userId: number,
    username: string,
  ): Promise<Record<string, unknown>> {
    const safeUsername: string = username.replace(/[^\x20-\x7E]/g, "").trim();
    return await this.nacosService.call({
      serviceName: "spring",
      method: "POST",
      path: "/users/github/token-ticket",
      body: {
        user_id: userId,
        username,
      },
      headers: {
        "X-Username": safeUsername,
      },
    });
  }
}
