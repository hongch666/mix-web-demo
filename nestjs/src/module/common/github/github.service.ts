import { Injectable } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import axios, { AxiosResponse } from "axios";
import { randomUUID } from "crypto";
import { Defaults, ErrorIds, Messages, RedisKeys } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { LoggerService } from "src/module/common/logger/logger.service";
import { SpringClientService } from "src/module/common/client/springClient.service";
import { RedisService } from "src/module/common/redis/redis.service";
import {
  GithubAuthorizeQueryDto,
  GithubCallbackQueryDto,
} from "./dto/github.dto";

/**
 * GitHub OAuth 配置，包含客户端凭据、授权与令牌端点地址及前端成功失败跳转页
 */
interface GithubOAuthConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  scope: string;
  authorizeUrl: string;
  accessTokenUrl: string;
  userApiUrl: string;
  emailsApiUrl: string;
  apiVersion: string;
  frontendSuccessUrl: string;
  frontendFailureUrl: string;
}

/**
 * 获取授权地址的结果，包含拼接好的授权 URL 与对应的 state 值
 */
interface GithubAuthorizeResult {
  authorizeUrl: string;
  state: string;
}

/**
 * GitHub 令牌接口的响应结构，包含访问令牌或错误码与错误描述
 */
interface GithubAccessTokenResponse {
  access_token?: string;
  scope?: string;
  token_type?: string;
  error?: string;
  errorDescription?: string;
  error_description?: string;
}

/**
 * GitHub 用户信息接口的响应结构，包含用户 ID、登录名、昵称、头像等字段
 */
interface GithubUserResponse {
  id: number;
  login: string;
  name?: string | null;
  email?: string | null;
  avatar_url?: string | null;
  html_url?: string | null;
}

/**
 * GitHub 用户邮箱接口的响应元素，包含邮箱地址及其主要与已验证标记
 */
interface GithubEmailResponse {
  email: string;
  primary: boolean;
  verified: boolean;
  visibility?: string | null;
}

/**
 * 存入 Redis 的 OAuth state 载荷，记录授权完成后要回跳的前端路径
 */
interface GithubStatePayload {
  redirect: string;
}

/**
 * GitHub OAuth 登录服务，负责生成授权地址、处理回调换取用户信息并创建登录票据
 */
@Injectable()
export class GithubService {
  private readonly githubConfig: GithubOAuthConfig;

  private readonly stateTtlSeconds = 600;

  constructor(
    private readonly configService: ConfigService,
    private readonly redisService: RedisService,
    private readonly springClientService: SpringClientService,
    private readonly logger: LoggerService,
  ) {
    this.githubConfig = this.buildGithubConfig();
  }

  /**
   * 校验 OAuth 配置后生成随机 state 存入 Redis，并拼接携带客户端信息的 GitHub 授权地址
   */
  async buildAuthorizeUrl(
    query: GithubAuthorizeQueryDto,
  ): Promise<GithubAuthorizeResult> {
    this.validateGithubConfig();

    const redisClient = this.redisService.getClient();
    if (!redisClient) {
      throw BusinessException.serviceUnavailable(
        Messages.GITHUB_REDIS_UNAVAILABLE,
      );
    }

    const state: string = randomUUID().replace(/-/g, "");
    const redirect: string = this.normalizeRedirect(query.redirect);
    const stateKey: string = RedisKeys.OAUTH_GITHUB_STATE(state);

    await redisClient.set(
      stateKey,
      JSON.stringify({ redirect }),
      "EX",
      this.stateTtlSeconds,
    );

    const authorizeUrl: URL = new URL(this.githubConfig.authorizeUrl);
    authorizeUrl.searchParams.set("client_id", this.githubConfig.clientId);
    authorizeUrl.searchParams.set(
      "redirect_uri",
      this.githubConfig.redirectUri,
    );
    authorizeUrl.searchParams.set("scope", this.githubConfig.scope);
    authorizeUrl.searchParams.set("state", state);
    authorizeUrl.searchParams.set("allow_signup", "true");

    return {
      authorizeUrl: authorizeUrl.toString(),
      state,
    };
  }

  /**
   * 处理 OAuth 回调的完整流程，校验 state、换取令牌、获取用户信息并在 Spring 侧落库后生成登录票据，失败时返回失败跳转地址
   */
  async handleCallback(query: GithubCallbackQueryDto): Promise<string> {
    try {
      this.validateGithubConfig();

      if (!query.code || !query.state) {
        throw BusinessException.unauthorized(
          Messages.GITHUB_AUTH_PARAMS_MISSING,
        );
      }

      const statePayload: GithubStatePayload = await this.consumeState(
        query.state,
      );

      if (query.error) {
        throw BusinessException.unauthorized(
          Messages.GITHUB_AUTH_CANCELLED_OR_FAILED,
        );
      }

      const accessToken: string = await this.exchangeCodeForAccessToken(
        query.code,
      );
      // profile 与 emails 为两个完全独立的 GitHub API 调用，Promise.all 并行降低延迟
      const [profileResult, emailResult] = await Promise.allSettled([
        this.fetchGithubProfile(accessToken),
        this.fetchPrimaryEmail(accessToken),
      ]);
      if (profileResult.status === "rejected") {
        throw profileResult.reason;
      }
      const githubProfile: GithubUserResponse = profileResult.value;
      const githubEmailFallback: string | null =
        emailResult.status === "fulfilled" ? emailResult.value : null;
      const githubEmail: string | null =
        githubProfile.email || githubEmailFallback;
      const userResult: Record<string, unknown> =
        await this.springClientService.findOrCreateGithubUser({
          github_id: String(githubProfile.id),
          github_login: githubProfile.login,
          github_name: githubProfile.name?.trim() || githubProfile.login,
          github_url:
            githubProfile.html_url ||
            `https://github.com/${githubProfile.login}`,
          avatar_url: githubProfile.avatar_url ?? null,
          email: githubEmail,
        });
      const user: { id: number; name: string } =
        SpringClientService.extractData<{ id: number; name: string }>(
          userResult,
        );
      const ticket: string = await this.createLoginTicket(user.id, user.name);
      return this.buildSuccessRedirectUrl(ticket, statePayload.redirect);
    } catch (error) {
      this.logger.error(
        `${Messages.GITHUB_LOGIN_PROCESS_FAILED_PREFIX}${error instanceof Error ? error.message : String(error)}`,
      );
      return this.buildFailureRedirectUrl();
    }
  }

  /**
   * 从配置服务读取 github.oauth 配置段并组装为完整的 OAuth 配置对象
   */
  private buildGithubConfig(): GithubOAuthConfig {
    const githubConfig =
      this.configService.get<Record<string, unknown>>("github") || {};
    const oauth = (githubConfig.oauth as Record<string, unknown>) || {};

    return {
      clientId: this.readGithubConfigString(oauth.clientId),
      clientSecret: this.readGithubConfigString(oauth.clientSecret),
      redirectUri: this.readGithubConfigString(oauth.redirectUri),
      scope: this.readGithubConfigString(oauth.scope),
      authorizeUrl: this.readGithubConfigString(oauth.authorizeUrl),
      accessTokenUrl: this.readGithubConfigString(oauth.accessTokenUrl),
      userApiUrl: this.readGithubConfigString(oauth.userApiUrl),
      emailsApiUrl: this.readGithubConfigString(oauth.emailsApiUrl),
      apiVersion: this.readGithubConfigString(oauth.apiVersion),
      frontendSuccessUrl: this.readGithubConfigString(oauth.frontendSuccessUrl),
      frontendFailureUrl: this.readGithubConfigString(oauth.frontendFailureUrl),
    };
  }

  /**
   * 将配置值规范化为去空格的字符串，非字符串类型转字符串，缺失时返回回退值
   */
  private readGithubConfigString(value: unknown, fallback = ""): string {
    if (typeof value === "string") {
      return value.trim();
    }

    if (
      typeof value === "number" ||
      typeof value === "boolean" ||
      typeof value === "bigint"
    ) {
      return String(value);
    }

    return fallback.trim();
  }

  /**
   * 校验 OAuth 配置必填项是否齐全，缺失任一项时抛出内部服务器错误
   */
  private validateGithubConfig(): void {
    const requiredFields: Array<{ value: string; name: string }> = [
      { value: this.githubConfig.clientId, name: "clientId" },
      { value: this.githubConfig.clientSecret, name: "clientSecret" },
      { value: this.githubConfig.redirectUri, name: "redirectUri" },
      { value: this.githubConfig.scope, name: "scope" },
      { value: this.githubConfig.authorizeUrl, name: "authorizeUrl" },
      { value: this.githubConfig.accessTokenUrl, name: "accessTokenUrl" },
      { value: this.githubConfig.userApiUrl, name: "userApiUrl" },
      { value: this.githubConfig.emailsApiUrl, name: "emailsApiUrl" },
      { value: this.githubConfig.apiVersion, name: "apiVersion" },
      {
        value: this.githubConfig.frontendSuccessUrl,
        name: "frontendSuccessUrl",
      },
      {
        value: this.githubConfig.frontendFailureUrl,
        name: "frontendFailureUrl",
      },
    ];

    const missingField: { value: string; name: string } | undefined =
      requiredFields.find(({ value }) => !value);
    if (missingField) {
      throw BusinessException.internalServerError(
        `${Messages.GITHUB_OAUTH_CONFIG_INCOMPLETE_PREFIX}${missingField.name}`,
      );
    }
  }

  /**
   * 读取并删除 Redis 中的 state 记录（一次性消费），校验其有效性并解析出回跳路径
   */
  private async consumeState(state: string): Promise<GithubStatePayload> {
    const redisClient = this.redisService.getClient();
    if (!redisClient) {
      throw BusinessException.serviceUnavailable(
        Messages.GITHUB_REDIS_STATE_UNAVAILABLE,
      );
    }

    const stateKey: string = RedisKeys.OAUTH_GITHUB_STATE(state);
    const storedState: string | null = await redisClient.get(stateKey);
    if (!storedState) {
      throw BusinessException.unauthorized(Messages.GITHUB_STATE_EXPIRED);
    }

    await redisClient.del(stateKey);

    try {
      return JSON.parse(storedState) as GithubStatePayload;
    } catch {
      throw BusinessException.unauthorized(Messages.GITHUB_STATE_PARSE_FAILED);
    }
  }

  /**
   * 用授权码调用 GitHub 令牌接口换取访问令牌，兼容 JSON 与表单两种响应格式并校验错误
   */
  private async exchangeCodeForAccessToken(code: string): Promise<string> {
    try {
      const response: AxiosResponse<GithubAccessTokenResponse | string> =
        await axios.post<GithubAccessTokenResponse>(
          this.githubConfig.accessTokenUrl,
          {
            client_id: this.githubConfig.clientId,
            client_secret: this.githubConfig.clientSecret,
            code,
            redirect_uri: this.githubConfig.redirectUri,
          },
          {
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
            timeout: Defaults.GITHUB_HTTP_TIMEOUT_MS,
            // 保留 4xx 作为业务响应，5xx 交给 axios-retry 自动重试
            validateStatus: (status: number) => status < 500,
          },
        );

      const responseData: unknown = response.data;
      let data: GithubAccessTokenResponse = {};
      if (responseData !== null && typeof responseData === "object") {
        data = responseData as GithubAccessTokenResponse;
      } else if (typeof responseData === "string") {
        try {
          data = JSON.parse(responseData) as GithubAccessTokenResponse;
        } catch {
          const formData: URLSearchParams = new URLSearchParams(responseData);
          data = {
            access_token: formData.get("access_token") || undefined,
            error: formData.get("error") || undefined,
            error_description: formData.get("error_description") || undefined,
          };
        }
      }
      const errorCode: string = data.error || "";
      const errorDescription: string =
        data.errorDescription || data.error_description || "";
      const contentType: string = String(
        response.headers["content-type"] || "",
      );

      if (
        response.status < 200 ||
        response.status >= 300 ||
        errorCode ||
        !data.access_token
      ) {
        this.logger.error(
          Messages.GITHUB_ACCESS_TOKEN_RESPONSE(
            response.status,
            errorCode,
            errorDescription,
            contentType,
          ),
        );
        throw BusinessException.badGateway(
          errorDescription || Messages.GITHUB_ACCESS_TOKEN_FAILED,
          ErrorIds.GITHUB_ACCESS_TOKEN_FAILED,
        );
      }

      return data.access_token;
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        this.logger.error(
          Messages.GITHUB_ACCESS_TOKEN_REQUEST_FAILED(
            error.code || "",
            error.message,
            error.response?.status,
          ),
        );
      }
      throw error;
    }
  }

  /**
   * 携带访问令牌调用 GitHub 用户信息接口，校验响应并返回用户资料
   */
  private async fetchGithubProfile(
    accessToken: string,
  ): Promise<GithubUserResponse> {
    try {
      const response: AxiosResponse<GithubUserResponse> =
        await axios.get<GithubUserResponse>(this.githubConfig.userApiUrl, {
          headers: {
            Accept: "application/vnd.github+json",
            Authorization: `Bearer ${accessToken}`,
            "X-GitHub-Api-Version": this.githubConfig.apiVersion,
          },
          timeout: Defaults.GITHUB_HTTP_TIMEOUT_MS,
          // 保留 4xx 作为业务响应，5xx 交给 axios-retry 自动重试
          validateStatus: (status: number) => status < 500,
        });

      if (response.status < 200 || response.status >= 300) {
        const responseData: unknown = response.data;
        const responseMessageValue: unknown =
          responseData !== null && typeof responseData === "object"
            ? (responseData as { message?: unknown }).message
            : undefined;
        const responseMessage: string =
          typeof responseMessageValue === "string" ? responseMessageValue : "";
        this.logger.error(
          Messages.GITHUB_USER_PROFILE_RESPONSE(
            response.status,
            responseMessage,
            String(response.headers["content-type"] || ""),
            String(response.headers["x-github-request-id"] || ""),
          ),
        );
        throw BusinessException.badGateway(
          Messages.GITHUB_USER_PROFILE_FAILED,
          ErrorIds.GITHUB_USER_PROFILE_FAILED,
        );
      }

      const data: GithubUserResponse = response.data;
      if (!data.id || !data.login) {
        this.logger.error(
          Messages.GITHUB_USER_PROFILE_RESPONSE(
            response.status,
            Messages.GITHUB_USER_PROFILE_MISSING_FIELDS,
            String(response.headers["content-type"] || ""),
            String(response.headers["x-github-request-id"] || ""),
          ),
        );
        throw BusinessException.badGateway(
          Messages.GITHUB_USER_PROFILE_INVALID,
          ErrorIds.GITHUB_USER_PROFILE_INVALID,
        );
      }

      return data;
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        this.logger.error(
          Messages.GITHUB_USER_PROFILE_REQUEST_FAILED(
            error.code || "",
            error.message,
            error.response?.status,
          ),
        );
      }
      throw error;
    }
  }

  /**
   * 携带访问令牌调用 GitHub 邮箱接口，返回主要且已验证的邮箱地址，失败时返回 null
   */
  private async fetchPrimaryEmail(accessToken: string): Promise<string | null> {
    const response: AxiosResponse<GithubEmailResponse[]> = await axios.get<
      GithubEmailResponse[]
    >(this.githubConfig.emailsApiUrl, {
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${accessToken}`,
        "X-GitHub-Api-Version": this.githubConfig.apiVersion,
      },
      timeout: Defaults.GITHUB_HTTP_TIMEOUT_MS,
      // 保留 4xx 作为业务响应，5xx 交给 axios-retry 自动重试
      validateStatus: (status: number) => status < 500,
    });

    if (response.status < 200 || response.status >= 300) {
      return null;
    }

    const data: GithubEmailResponse[] = response.data;
    const primaryEmail: GithubEmailResponse | undefined = data.find(
      (item: GithubEmailResponse) => item.primary && item.verified,
    );
    return primaryEmail?.email ?? null;
  }

  /**
   * 调用 Spring 服务为 GitHub 用户创建登录令牌票据，失败或票据缺失时抛出网关错误
   */
  private async createLoginTicket(
    userId: number,
    username: string,
  ): Promise<string> {
    const response: { data?: unknown; code?: number } =
      await this.springClientService.createTokenTicket(userId, username);

    if (response.code !== 200) {
      throw BusinessException.badGateway(
        Messages.GITHUB_SPRING_TOKEN_TICKET_FAILED,
        ErrorIds.GITHUB_TOKEN_TICKET_FAILED,
      );
    }

    const data: Record<string, unknown> | undefined = response.data as
      | Record<string, unknown>
      | undefined;
    const ticket: string | undefined = data?.ticket as string | undefined;
    if (!ticket) {
      throw BusinessException.badGateway(
        Messages.GITHUB_SPRING_TOKEN_TICKET_MISSING,
        ErrorIds.GITHUB_TOKEN_TICKET_FAILED,
      );
    }

    return ticket;
  }

  /**
   * 在配置的前端成功页地址上附加 ticket 与 redirect 参数，拼出登录成功回跳地址
   */
  private buildSuccessRedirectUrl(ticket: string, redirect: string): string {
    const successUrl = new URL(this.githubConfig.frontendSuccessUrl);
    successUrl.searchParams.set("ticket", ticket);
    successUrl.searchParams.set("redirect", this.normalizeRedirect(redirect));
    return successUrl.toString();
  }

  /**
   * 在配置的前端失败页地址上附加 oauth_error 参数，拼出登录失败回跳地址
   */
  private buildFailureRedirectUrl(): string {
    const failureUrl = new URL(this.githubConfig.frontendFailureUrl);
    failureUrl.searchParams.set("oauth_error", "github");
    return failureUrl.toString();
  }

  /**
   * 规范化前端回跳路径，只允许站内相对路径，外部链接与空值统一回退到根路径
   */
  private normalizeRedirect(redirect?: string): string {
    const fallbackRedirect = "/";
    if (!redirect) {
      return fallbackRedirect;
    }

    const trimmedRedirect = redirect.trim();
    if (!trimmedRedirect) {
      return fallbackRedirect;
    }

    if (
      trimmedRedirect.startsWith("http://") ||
      trimmedRedirect.startsWith("https://") ||
      trimmedRedirect.startsWith("//")
    ) {
      return fallbackRedirect;
    }

    return trimmedRedirect.startsWith("/")
      ? trimmedRedirect
      : `/${trimmedRedirect}`;
  }
}
