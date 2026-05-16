import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios, { AxiosResponse } from 'axios';
import { randomUUID } from 'crypto';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import { logger } from 'src/common/utils/writeLog';
import { SpringClientService } from 'src/modules/client/springClient.service';
import { RedisService } from 'src/modules/redis/redis.service';
import { RemoteUser, UserService } from 'src/modules/user/user.service';
import {
  GithubAuthorizeQueryDto,
  GithubCallbackQueryDto,
} from './dto/github.dto';

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

interface GithubAuthorizeResult {
  authorizeUrl: string;
  state: string;
}

interface GithubAccessTokenResponse {
  access_token?: string;
  scope?: string;
  token_type?: string;
  error?: string;
  error_description?: string;
}

interface GithubUserResponse {
  id: number;
  login: string;
  name?: string | null;
  email?: string | null;
  avatar_url?: string | null;
  html_url?: string | null;
}

interface GithubEmailResponse {
  email: string;
  primary: boolean;
  verified: boolean;
  visibility?: string | null;
}

interface GithubStatePayload {
  redirect: string;
}

@Injectable()
export class GithubService {
  private readonly githubConfig: GithubOAuthConfig;

  private readonly stateTtlSeconds = 600;

  constructor(
    private readonly configService: ConfigService,
    private readonly redisService: RedisService,
    private readonly userService: UserService,
    private readonly springClientService: SpringClientService,
  ) {
    this.githubConfig = this.buildGithubConfig();
  }

  async buildAuthorizeUrl(
    query: GithubAuthorizeQueryDto,
  ): Promise<GithubAuthorizeResult> {
    this.validateGithubConfig();

    const redisClient = this.redisService.getClient();
    if (!redisClient) {
      throw BusinessException.serviceUnavailable(
        Constants.GITHUB_REDIS_UNAVAILABLE,
      );
    }

    const state: string = randomUUID().replace(/-/g, '');
    const redirect: string = this.normalizeRedirect(query.redirect);
    const stateKey: string = this.buildStateKey(state);

    await redisClient.set(
      stateKey,
      JSON.stringify({ redirect }),
      'EX',
      this.stateTtlSeconds,
    );

    const authorizeUrl: URL = new URL(this.githubConfig.authorizeUrl);
    authorizeUrl.searchParams.set('client_id', this.githubConfig.clientId);
    authorizeUrl.searchParams.set(
      'redirect_uri',
      this.githubConfig.redirectUri,
    );
    authorizeUrl.searchParams.set('scope', this.githubConfig.scope);
    authorizeUrl.searchParams.set('state', state);
    authorizeUrl.searchParams.set('allow_signup', 'true');

    return {
      authorizeUrl: authorizeUrl.toString(),
      state,
    };
  }

  async handleCallback(query: GithubCallbackQueryDto): Promise<string> {
    try {
      this.validateGithubConfig();

      if (!query.code || !query.state) {
        throw BusinessException.unauthorized(
          Constants.GITHUB_AUTH_PARAMS_MISSING,
        );
      }

      const statePayload: GithubStatePayload = await this.consumeState(
        query.state,
      );

      if (query.error) {
        throw BusinessException.unauthorized(
          Constants.GITHUB_AUTH_CANCELLED_OR_FAILED,
        );
      }

      const accessToken: string = await this.exchangeCodeForAccessToken(
        query.code,
      );
      const githubProfile: GithubUserResponse =
        await this.fetchGithubProfile(accessToken);
      const githubEmail: string | null =
        githubProfile.email || (await this.fetchPrimaryEmail(accessToken));
      const user: RemoteUser = await this.userService.findOrCreateGithubUser({
        githubId: String(githubProfile.id),
        githubLogin: githubProfile.login,
        githubName: githubProfile.name?.trim() || githubProfile.login,
        githubUrl:
          githubProfile.html_url || `https://github.com/${githubProfile.login}`,
        avatarUrl: githubProfile.avatar_url ?? null,
        email: githubEmail,
      });
      const ticket: string = await this.createLoginTicket(user.id, user.name);
      return this.buildSuccessRedirectUrl(ticket, statePayload.redirect);
    } catch (error) {
      logger.error(
        `${Constants.GITHUB_LOGIN_PROCESS_FAILED_PREFIX}${error instanceof Error ? error.message : String(error)}`,
      );
      return this.buildFailureRedirectUrl();
    }
  }

  private buildGithubConfig(): GithubOAuthConfig {
    const githubConfig =
      this.configService.get<Record<string, unknown>>('github') || {};
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
      frontendSuccessUrl: this.readGithubConfigString(
        oauth.frontendSuccessUrl,
      ),
      frontendFailureUrl: this.readGithubConfigString(
        oauth.frontendFailureUrl,
      ),
    };
  }

  private readGithubConfigString(value: unknown, fallback = ''): string {
    if (typeof value === 'string') {
      return value.trim();
    }

    if (
      typeof value === 'number' ||
      typeof value === 'boolean' ||
      typeof value === 'bigint'
    ) {
      return String(value);
    }

    return fallback.trim();
  }

  private validateGithubConfig(): void {
    const requiredFields: Array<{ value: string; name: string }> = [
      { value: this.githubConfig.clientId, name: 'clientId' },
      { value: this.githubConfig.clientSecret, name: 'clientSecret' },
      { value: this.githubConfig.redirectUri, name: 'redirectUri' },
      { value: this.githubConfig.scope, name: 'scope' },
      { value: this.githubConfig.authorizeUrl, name: 'authorizeUrl' },
      { value: this.githubConfig.accessTokenUrl, name: 'accessTokenUrl' },
      { value: this.githubConfig.userApiUrl, name: 'userApiUrl' },
      { value: this.githubConfig.emailsApiUrl, name: 'emailsApiUrl' },
      { value: this.githubConfig.apiVersion, name: 'apiVersion' },
      {
        value: this.githubConfig.frontendSuccessUrl,
        name: 'frontendSuccessUrl',
      },
      {
        value: this.githubConfig.frontendFailureUrl,
        name: 'frontendFailureUrl',
      },
    ];

    const missingField: { value: string; name: string } | undefined =
      requiredFields.find(({ value }) => !value);
    if (missingField) {
      throw BusinessException.internalServerError(
        `${Constants.GITHUB_OAUTH_CONFIG_INCOMPLETE_PREFIX}${missingField.name}`,
      );
    }
  }

  private async consumeState(state: string): Promise<GithubStatePayload> {
    const redisClient = this.redisService.getClient();
    if (!redisClient) {
      throw BusinessException.serviceUnavailable(
        Constants.GITHUB_REDIS_STATE_UNAVAILABLE,
      );
    }

    const stateKey: string = this.buildStateKey(state);
    const storedState: string | null = await redisClient.get(stateKey);
    if (!storedState) {
      throw BusinessException.unauthorized(Constants.GITHUB_STATE_EXPIRED);
    }

    await redisClient.del(stateKey);

    try {
      return JSON.parse(storedState) as GithubStatePayload;
    } catch {
      throw BusinessException.unauthorized(Constants.GITHUB_STATE_PARSE_FAILED);
    }
  }

  private async exchangeCodeForAccessToken(code: string): Promise<string> {
    const response: AxiosResponse<GithubAccessTokenResponse> =
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
            Accept: 'application/json',
            'Content-Type': 'application/json',
          },
          validateStatus: () => true,
        },
      );

    const data: GithubAccessTokenResponse = response.data;
    if (
      response.status < 200 ||
      response.status >= 300 ||
      data.error ||
      !data.access_token
    ) {
      throw BusinessException.badGateway(
        data.error_description || Constants.GITHUB_ACCESS_TOKEN_FAILED,
        'GITHUB_ACCESS_TOKEN_FAILED',
      );
    }

    return data.access_token;
  }

  private async fetchGithubProfile(
    accessToken: string,
  ): Promise<GithubUserResponse> {
    const response: AxiosResponse<GithubUserResponse> =
      await axios.get<GithubUserResponse>(this.githubConfig.userApiUrl, {
        headers: {
          Accept: 'application/vnd.github+json',
          Authorization: `Bearer ${accessToken}`,
          'X-GitHub-Api-Version': this.githubConfig.apiVersion,
        },
        validateStatus: () => true,
      });

    if (response.status < 200 || response.status >= 300) {
      throw BusinessException.badGateway(
        Constants.GITHUB_USER_PROFILE_FAILED,
        'GITHUB_USER_PROFILE_FAILED',
      );
    }

    const data: GithubUserResponse = response.data;
    if (!data.id || !data.login) {
      throw BusinessException.badGateway(
        Constants.GITHUB_USER_PROFILE_INVALID,
        'GITHUB_USER_PROFILE_INVALID',
      );
    }

    return data;
  }

  private async fetchPrimaryEmail(accessToken: string): Promise<string | null> {
    const response: AxiosResponse<GithubEmailResponse[]> = await axios.get<
      GithubEmailResponse[]
    >(this.githubConfig.emailsApiUrl, {
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${accessToken}`,
        'X-GitHub-Api-Version': this.githubConfig.apiVersion,
      },
      validateStatus: () => true,
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

  private async createLoginTicket(
    userId: number,
    username: string,
  ): Promise<string> {
    const response: { data?: unknown; code?: number } =
      await this.springClientService.createTokenTicket(userId, username);

    if (response.code !== 200) {
      throw BusinessException.badGateway(
        Constants.GITHUB_SPRING_TOKEN_TICKET_FAILED,
        'GITHUB_TOKEN_TICKET_FAILED',
      );
    }

    const data: Record<string, unknown> | undefined = response.data as
      | Record<string, unknown>
      | undefined;
    const ticket: string | undefined = data?.ticket as string | undefined;
    if (!ticket) {
      throw BusinessException.badGateway(
        Constants.GITHUB_SPRING_TOKEN_TICKET_MISSING,
        'GITHUB_TOKEN_TICKET_FAILED',
      );
    }

    return ticket;
  }

  private buildSuccessRedirectUrl(ticket: string, redirect: string): string {
    const successUrl = new URL(this.githubConfig.frontendSuccessUrl);
    successUrl.searchParams.set('ticket', ticket);
    successUrl.searchParams.set('redirect', this.normalizeRedirect(redirect));
    return successUrl.toString();
  }

  private buildFailureRedirectUrl(): string {
    const failureUrl = new URL(this.githubConfig.frontendFailureUrl);
    failureUrl.searchParams.set('oauthError', 'github');
    return failureUrl.toString();
  }

  private normalizeRedirect(redirect?: string): string {
    const fallbackRedirect = '/';
    if (!redirect) {
      return fallbackRedirect;
    }

    const trimmedRedirect = redirect.trim();
    if (!trimmedRedirect) {
      return fallbackRedirect;
    }

    if (
      trimmedRedirect.startsWith('http://') ||
      trimmedRedirect.startsWith('https://') ||
      trimmedRedirect.startsWith('//')
    ) {
      return fallbackRedirect;
    }

    return trimmedRedirect.startsWith('/')
      ? trimmedRedirect
      : `/${trimmedRedirect}`;
  }

  private buildStateKey(state: string): string {
    return `oauth:github:state:${state}`;
  }
}
