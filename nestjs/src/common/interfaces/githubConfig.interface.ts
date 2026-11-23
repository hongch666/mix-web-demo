/**
 * GitHub OAuth 配置，包含客户端凭据、授权与令牌端点地址及前端成功失败跳转页
 */
export interface GithubOAuthConfig {
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
