import { Injectable } from '@nestjs/common';
import { SpringClientService } from 'src/modules/client/springClient.service';

export interface GithubUserProfile {
  githubId: string;
  githubLogin: string;
  githubName: string | null;
  githubUrl: string | null;
  avatarUrl: string | null;
  email: string | null;
}

export interface RemoteUser {
  id: number;
  name: string;
  role?: string;
  img?: string;
  githubLogin?: string;
}

@Injectable()
export class UserService {
  constructor(private readonly springClientService: SpringClientService) {}

  async getUserById(id: number): Promise<RemoteUser | null> {
    const response = await this.springClientService.getUserById(id);
    return (response.data as RemoteUser | null) ?? null;
  }

  async getUsersByIds(ids: number[]): Promise<Map<number, RemoteUser>> {
    const validIds = Array.from(
      new Set(ids.filter((id) => Number.isFinite(id) && id > 0)),
    );
    if (validIds.length === 0) {
      return new Map();
    }
    const response = await this.springClientService.getUsersByIds(validIds);
    const users = (response.data as RemoteUser[] | null) ?? [];
    return new Map(users.map((user) => [user.id, user]));
  }

  async getUsersByName(name: string): Promise<RemoteUser[]> {
    const response = await this.springClientService.searchUsers(name);
    const data = response.data as { list?: RemoteUser[] } | undefined;
    return data?.list ?? [];
  }

  async findOrCreateGithubUser(
    profile: GithubUserProfile,
  ): Promise<RemoteUser> {
    const response = await this.springClientService.upsertGithubUser({
      githubId: profile.githubId,
      githubLogin: profile.githubLogin,
      githubName: profile.githubName,
      githubUrl: profile.githubUrl,
      avatarUrl: profile.avatarUrl,
      email: profile.email,
    });
    const data = response.data as {
      userId: number;
      username: string;
      role: string;
    };
    return {
      id: data.userId,
      name: data.username,
      role: data.role,
    };
  }

  async isAdminUser(userId: number): Promise<boolean> {
    const response = await this.springClientService.getUserRole(userId);
    const data = response.data as { admin?: boolean } | undefined;
    return Boolean(data?.admin);
  }
}
