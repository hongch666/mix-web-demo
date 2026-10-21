package com.hcsy.spring.web.controller;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

import org.springdoc.core.annotations.ParameterObject;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.application.service.ImageCaptchaService;
import com.hcsy.spring.application.service.TokenService;
import com.hcsy.spring.application.service.UserService;
import com.hcsy.spring.common.constants.BusinessType;
import com.hcsy.spring.common.constants.HeaderNames;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.ParamSource;
import com.hcsy.spring.common.constants.SyncChangeType;
import com.hcsy.spring.common.constants.SyncResource;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.entity.dto.BatchIdsDTO;
import com.hcsy.spring.entity.dto.EmailCodeSendDTO;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.GithubTokenExchangeDTO;
import com.hcsy.spring.entity.dto.GithubTokenTicketCreateDTO;
import com.hcsy.spring.entity.dto.GithubUserInternalDTO;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.RefreshTokenDTO;
import com.hcsy.spring.entity.dto.ResetPasswordDTO;
import com.hcsy.spring.entity.dto.UserCreateDTO;
import com.hcsy.spring.entity.dto.UserQueryDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.dto.UserUpdateDTO;
import com.hcsy.spring.entity.vo.GithubTokenTicketVO;
import com.hcsy.spring.entity.vo.ImageCaptchaVO;
import com.hcsy.spring.entity.vo.KickOtherDevicesVO;
import com.hcsy.spring.entity.vo.TokenRefreshVO;
import com.hcsy.spring.entity.vo.UserListVO;
import com.hcsy.spring.entity.vo.UserLoginVO;
import com.hcsy.spring.entity.vo.UserSyncVO;
import com.hcsy.spring.entity.vo.UserVO;
import com.hcsy.spring.web.logging.annotation.ApiLog;
import com.hcsy.spring.web.security.annotation.RequireInternalToken;
import com.hcsy.spring.web.security.annotation.RequirePermission;
import com.hcsy.spring.web.sync.annotation.DataSync;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.headers.Header;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

/**
 * 用户控制器，聚合 /users 下的注册登录（含邮箱、GitHub与票据兑换）、验证码、用户增删改查、令牌刷新与多设备管理等接口
 */
@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@Tag(name = "用户模块", description = "用户管理功能相关API，包括用户注册、登录、信息管理、验证码等")
public class UserController {
    private final UserService userService;
    private final TokenService tokenService;
    private final ImageCaptchaService imageCaptchaService;

    /**
     * GET /users 接口，分页返回用户列表并支持用户名模糊查询，实时附带登录状态与设备数，仅管理员可用
     */
    @GetMapping()
    @Operation(summary = "获取用户信息", description = "分页获取用户信息列表，并支持用户名模糊查询，实时返回用户登录状态和设备数")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.USER, paramSource = ParamSource.QUERY)
    @ApiLog("获取用户信息")
    public Mono<Result<UserListVO>> listUsers(@ParameterObject @ModelAttribute UserQueryDTO queryDTO) {
        return userService.listUsersWithFilter(queryDTO.getPage(), queryDTO.getSize(), queryDTO.getUsername())
            .map(Result::success);
    }

    /**
     * GET /users/all 接口，不分页返回全部用户列表
     */
    @GetMapping("/all")
    @Operation(summary = "获取所有用户", description = "获取所有用户列表（不分页）")
    @ApiLog("获取所有用户")
    public Mono<Result<UserListVO>> getAllUsers() {
        return userService.getAllUsers(null).map(Result::success);
    }

    /**
     * GET /users/ai 接口，不分页返回 role 为 ai 的AI用户列表
     */
    @GetMapping("/ai")
    @Operation(summary = "获取所有AI用户", description = "获取 role 为 ai 的用户列表，不分页")
    @ApiLog("获取所有AI用户")
    public Mono<Result<UserListVO>> getAllAiUsers() {
        return userService.getAllAiUsers().map(Result::success);
    }

    /**
     * POST /users 接口，管理员创建新用户并返回新用户ID，未传密码时使用配置中的默认密码
     */
    @PostMapping
    @Operation(summary = "新增用户", description = "创建新用户，如果不传密码则使用配置中的默认密码")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.USER, paramSource = ParamSource.BODY,
        paramName = "id")
    @DataSync(resource = SyncResource.USER, changeType = SyncChangeType.INSERT, description = "新增用户后同步图谱与数仓")
    @ApiLog(value = "新增用户", excludeFields = { "password" })
    public Mono<Result<Long>> addUser(@Valid @RequestBody UserCreateDTO userDto) {
        return userService.createUser(userDto).map(user -> Result.success(user.getId()));
    }

    /**
     * DELETE /users/{id} 接口，按ID删除用户及其登录状态记录，仅管理员可用
     */
    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.USER, paramSource = ParamSource.PATH_SINGLE,
        paramName = "id")
    @DataSync(resource = SyncResource.USER, changeType = SyncChangeType.DELETE, description = "删除用户后同步图谱与数仓")
    @ApiLog("删除用户")
    public Mono<Result<Void>> deleteUser(@PathVariable Long id) {
        return userService.deleteUserAndStatusById(id).thenReturn(Result.<Void>success());
    }

    /**
     * DELETE /users/batch/{ids} 接口，按逗号分隔的ID列表批量删除用户及其登录状态，仅管理员可用
     */
    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除用户", description = "根据id数组批量删除用户，多个id用英文逗号分隔")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.USER, paramSource = ParamSource.PATH_SINGLE,
        paramName = "ids")
    @DataSync(resource = SyncResource.USER, changeType = SyncChangeType.DELETE, description = "批量删除用户后同步图谱与数仓")
    @ApiLog("批量删除用户")
    public Mono<Result<Void>> deleteUsers(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
            .map(String::trim)
            .filter(s -> !s.isEmpty())
            .map(Long::valueOf)
            .toList();
        return userService.deleteUsersAndStatusByIds(idList).thenReturn(Result.<Void>success());
    }

    /**
     * GET /users/{id} 接口，按ID返回用户详情及其登录状态与在线设备数，不存在时返回404
     */
    @GetMapping("/{id}")
    @Operation(summary = "查询用户", description = "根据id查询用户，返回用户信息及其登录状态和设备数")
    @ApiLog("查询用户")
    public Mono<Result<UserVO>> getUserById(@PathVariable Long id) {
        return userService.getUserDetail(id)
            .map(Result::success)
            .defaultIfEmpty(Result.<UserVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    /**
     * PUT /users 接口，根据更新DTO修改用户信息，需管理员或本人权限
     */
    @PutMapping
    @Operation(summary = "修改用户", description = "通过请求体修改用户信息")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = BusinessType.USER, paramSource = ParamSource.BODY, paramName = "id")
    @DataSync(resource = SyncResource.USER, changeType = SyncChangeType.UPDATE, description = "修改用户后同步图谱与数仓")
    @ApiLog("修改用户")
    public Mono<Result<Void>> updateUser(@Valid @RequestBody UserUpdateDTO userDto) {
        return userService.updateUserInfo(userDto).thenReturn(Result.<Void>success());
    }

    /**
     * PUT /users/status/{id} 接口，按用户ID修改存储在Redis中的用户状态
     */
    @PutMapping("/status/{id}")
    @Operation(summary = "修改用户状态", description = "根据用户ID修改用户状态（存储在Redis中）")
    @RequirePermission(roles = {
        "admin" }, allowSelf = true, businessType = BusinessType.USER, paramSource = ParamSource.PATH_SINGLE,
        paramName = "id")
    @ApiLog("修改用户状态")
    public Mono<Result<Void>> updateUserStatus(@PathVariable Long id, @RequestParam String status) {
        return userService.updateUserStatus(id, status).thenReturn(Result.<Void>success());
    }

    /**
     * GET /users/captcha 接口，生成图形验证码，返回验证码ID与base64图片数据，验证码缓存5分钟后过期
     */
    @GetMapping("/captcha")
    @Operation(summary = "获取图形验证码", description = "生成图形验证码，返回验证码ID和base64图片数据，验证码缓存到Redis并在5分钟后过期")
    @ApiLog("获取图形验证码")
    public Mono<Result<ImageCaptchaVO>> getImageCaptcha() {
        return imageCaptchaService.createCaptcha().map(Result::success);
    }

    /**
     * POST /users/login 接口，用户名密码登录，校验图形验证码后返回JWT令牌并将会话写入Redis
     */
    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "根据用户名和密码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog(value = "用户登录", excludeFields = { "password" })
    public Mono<Result<UserLoginVO>> login(@Valid @RequestBody LoginDTO loginDTO) {
        return userService.login(loginDTO).map(Result::success);
    }

    /**
     * GET /users/internal/auth/validate 接口，供网关校验访问令牌，校验通过后以 X-User-Id、X-Username、X-Session-Id 响应头返回用户身份
     */
    @GetMapping("/internal/auth/validate")
    @Operation(summary = "校验网关访问令牌", description = "校验访问令牌并返回用户身份请求头")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "校验通过，用户身份通过响应头返回，响应体为空", headers = {
            @Header(name = "X-User-Id", description = "用户ID", schema = @Schema(implementation = String.class)),
            @Header(name = "X-Username", description = "用户名", schema = @Schema(implementation = String.class)),
            @Header(name = "X-Session-Id", description = "会话ID", schema = @Schema(implementation = String.class)) }) })
    public Mono<ResponseEntity<Void>> validateGatewayAccessToken(
        @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String authorization,
        @RequestHeader(value = HeaderNames.ACCESS_TOKEN, required = false) String accessToken,
        @RequestHeader(value = HeaderNames.FORWARDED_URI, required = false) String forwardedUri) {
        return tokenService.validateGatewayAccessToken(authorization, accessToken, forwardedUri)
            .map(identity -> ResponseEntity.ok()
                .header(HeaderNames.USER_ID, String.valueOf(identity.getUserId()))
                .header(HeaderNames.USERNAME, identity.getUsername())
                .header(HeaderNames.SESSION_ID, identity.getSessionId())
                .build());
    }

    /**
     * POST /users/email-login 接口，通过邮箱与验证码登录，成功后返回JWT令牌并将会话写入Redis
     */
    @PostMapping("/email-login")
    @Operation(summary = "邮箱验证码登录", description = "通过邮箱和验证码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog(value = "邮箱验证码登录", excludeFields = { "verificationCode" })
    public Mono<Result<UserLoginVO>> emailLogin(@Valid @RequestBody EmailLoginDTO emailLoginDTO) {
        return userService.emailLogin(emailLoginDTO).map(Result::success);
    }

    /**
     * POST /users/github/token-ticket 内部接口，GitHub回调成功后生成本站一次性登录票据
     */
    @PostMapping("/github/token-ticket")
    @Operation(summary = "生成 GitHub 登录票据", description = "在 GitHub 回调成功后生成本站登录票据")
    @RequireInternalToken
    @ApiLog("生成 GitHub 登录票据")
    public Mono<Result<GithubTokenTicketVO>> createGithubTokenTicket(
        @Valid @RequestBody GithubTokenTicketCreateDTO dto) {
        return userService.createGithubTokenTicket(dto).map(Result::success);
    }

    /**
     * POST /users/github/token 接口，前端使用一次性ticket换取本站登录Token，成功后立即删除ticket防止重放
     */
    @PostMapping("/github/token")
    @Operation(summary = "获取 GitHub 登录 Token", description = "前端使用一次性 ticket 换取本站登录 token，成功后立即删除 ticket")
    @ApiLog(value = "获取 GitHub 登录 Token", excludeFields = { "ticket" })
    public Mono<Result<UserLoginVO>> exchangeGithubToken(@Valid @RequestBody GithubTokenExchangeDTO dto) {
        return userService.exchangeGithubTokenTicket(dto).map(Result::success);
    }

    /**
     * POST /users/logout 接口，从上下文中的access token解析会话并从Redis清除，实现当前设备登出
     */
    @PostMapping("/logout")
    @Operation(summary = "用户登出", description = "用户登出，从当前 access token 解析 session 并清除")
    @ApiLog("用户登出")
    public Mono<Result<Void>> logout() {
        return Mono.deferContextual(ctx -> {
            String accessToken = UserContext.getToken(ctx);
            if (accessToken == null) {
                return Mono.just(Result.<Void>error(HttpCode.UNAUTHORIZED, Messages.GET_USER_TOKEN_ID));
            }
            return tokenService.removeSessionByAccessToken(accessToken).thenReturn(Result.<Void>success());
        });
    }

    /**
     * POST /users/token/refresh 接口，使用refresh token轮换生成新的access token与refresh token
     */
    @PostMapping("/token/refresh")
    @Operation(summary = "刷新 Token", description = "使用 refresh token 刷新 access token 和 refresh token，支持 token 轮换")
    @ApiLog(value = "刷新 Token", excludeFields = { "refreshToken" })
    public Mono<Result<TokenRefreshVO>> refreshToken(@Valid @RequestBody RefreshTokenDTO refreshTokenDTO) {
        return tokenService.refreshToken(refreshTokenDTO.getRefreshToken()).map(Result::success);
    }

    /**
     * 管理员手动下线用户
     */
    @PostMapping("/force-logout/{user_id}")
    @Operation(summary = "手动下线用户", description = "管理员操作：将指定用户的所有登录会话强制下线")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.USER, paramSource = ParamSource.PATH_SINGLE,
        paramName = "user_id")
    @ApiLog("手动下线用户")
    public Mono<Result<Void>> forceLogoutUser(@PathVariable("user_id") Long userId) {
        return userService.forceLogoutUser(userId)
            .map(exists -> exists
                ? Result.<Void>success()
                : Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    /**
     * POST /users/kick-other-devices 接口，清除当前用户除本次请求令牌外的所有其他设备会话并返回被踢出的设备信息
     */
    @PostMapping("/kick-other-devices")
    @Operation(summary = "踢出其他设备", description = "清除当前用户除本次请求携带的 access token 之外的所有 session（保留当前设备）")
    @ApiLog("踢出其他设备")
    public Mono<Result<KickOtherDevicesVO>> kickOtherDevices() {
        return Mono.deferContextual(ctx -> {
            String token = UserContext.getToken(ctx);
            Long userId = UserContext.getUserId(ctx);

            if (token == null || userId == null) {
                return Mono.just(Result.<KickOtherDevicesVO>error(HttpCode.UNAUTHORIZED, Messages.GET_USER_TOKEN_ID));
            }

            return userService.kickOtherDevices(userId, token).map(Result::success);
        });
    }

    /**
     * POST /users/register 接口，通过邮箱验证码校验身份后注册新用户并返回新用户ID
     */
    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "注册新用户，需要提供邮箱验证码")
    @DataSync(resource = SyncResource.USER, changeType = SyncChangeType.INSERT, description = "用户注册后同步图谱与数仓")
    @ApiLog(value = "用户注册", excludeFields = { "password", "verificationCode" })
    public Mono<Result<Long>> registerUser(@Valid @RequestBody UserRegisterDTO registerDto) {
        return userService.registerUser(registerDto).map(user -> Result.success(user.getId()));
    }

    /**
     * POST /users/email/send 接口，向指定邮箱发送验证码，支持注册与登录两种场景并按邮箱状态返回不同错误码
     */
    @PostMapping("/email/send")
    @Operation(summary = "发送邮箱验证码", description = "向指定邮箱发送验证码，支持注册(register)和登录(login)两种场景")
    @ApiLog("发送邮箱验证码")
    public Mono<Result<Void>> sendVerificationCode(@RequestParam(required = false) String email,
        @RequestParam(required = false) String type,
        @RequestBody(required = false) EmailCodeSendDTO body) {
        String resolvedEmail = email;
        String resolvedType = type;
        if (body != null) {
            resolvedEmail = resolvedEmail == null || resolvedEmail.isBlank() ? body.getEmail() : resolvedEmail;
            resolvedType = resolvedType == null || resolvedType.isBlank() ? body.getType() : resolvedType;
        }
        resolvedType = resolvedType == null || resolvedType.isBlank() ? "register" : resolvedType;
        return userService.sendVerificationCode(resolvedEmail, resolvedType)
            .map(outcome -> switch (outcome) {
                case SENT -> Result.<Void>success();
                case INVALID_EMAIL -> Result.<Void>error(HttpCode.UNPROCESSABLE_ENTITY, Messages.EMAIL);
                case INVALID_TYPE -> Result.<Void>error(HttpCode.BAD_REQUEST, Messages.VERIFY_CODE_UNSUPPORT);
                case EMAIL_EXISTS -> Result.<Void>error(HttpCode.CONFLICT, Messages.EMAIL_REGISTER);
                case EMAIL_NOT_FOUND -> Result.<Void>error(HttpCode.NOT_FOUND, Messages.EMAIL_UNREGISTER);
            });
    }

    /**
     * POST /users/reset-password 接口，用户通过邮箱验证码验证身份后重置密码
     */
    @PostMapping("/reset-password")
    @Operation(summary = "通过邮箱验证码重置密码", description = "用户通过邮箱验证码验证身份后重置密码")
    @ApiLog(value = "重置密码", excludeFields = { "newPassword", "verificationCode" })
    public Mono<Result<Void>> resetPassword(@Valid @RequestBody ResetPasswordDTO resetPasswordDTO) {
        return userService.resetPassword(resetPasswordDTO).thenReturn(Result.<Void>success());
    }

    /**
     * POST /users/admin/reset-all-passwords 接口，管理员将所有用户密码批量重置为配置中的重置密码
     */
    @PostMapping("/admin/reset-all-passwords")
    @Operation(summary = "管理员重置所有用户密码", description = "管理员操作：将所有用户密码重置为配置中的重置密码")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.USER, paramSource = ParamSource.BODY,
        paramName = "id")
    @ApiLog("重置所有用户密码")
    public Mono<Result<Void>> resetAllPasswords() {
        return userService.resetAllPasswords().thenReturn(Result.<Void>success());
    }

    /**
     * POST /users/admin/reset-password/{user_id} 接口，管理员将指定用户的密码重置为配置中的重置密码
     */
    @PostMapping("/admin/reset-password/{user_id}")
    @Operation(summary = "管理员重置指定用户密码", description = "管理员操作：将指定用户ID的密码重置为配置中的重置密码")
    @RequirePermission(roles = { "admin" }, businessType = BusinessType.USER, paramSource = ParamSource.PATH_SINGLE,
        paramName = "user_id")
    @ApiLog("重置指定用户密码")
    public Mono<Result<Void>> resetUserPassword(@PathVariable("user_id") Long userId) {
        return userService.resetUserPassword(userId).thenReturn(Result.<Void>success());
    }

    /**
     * POST /users/batch 内部接口，按ID列表批量返回用户信息
     */
    @PostMapping("/batch")
    @Operation(summary = "批量查询用户（内部）", description = "根据ID列表批量查询用户，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部批量查询用户")
    public Mono<Result<List<UserVO>>> getUserByIds(@Valid @RequestBody BatchIdsDTO dto) {
        return userService.listByIds(dto.getIds())
            .collectList()
            .map(users -> users.stream()
                .map(user -> BeanUtil.copyProperties(user, UserVO.class))
                .collect(Collectors.toList()))
            .map(Result::success);
    }

    /**
     * GET /users/by-name 内部接口，按用户名或GitHub登录名模糊搜索用户
     */
    @GetMapping("/by-name")
    @Operation(summary = "根据用户名模糊搜索用户（内部）", description = "根据用户名或GitHub登录名模糊搜索，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部搜索用户")
    public Mono<Result<List<UserVO>>> getUsersByName(@RequestParam String name) {
        return userService.listAllUserByUsername(name)
            .collectList()
            .map(users -> users.stream()
                .map(user -> BeanUtil.copyProperties(user, UserVO.class))
                .collect(Collectors.toList()))
            .map(Result::success);
    }

    /**
     * POST /users/github-user 内部接口，GitHub OAuth登录后创建或更新用户并返回用户信息
     */
    @PostMapping("/github-user")
    @Operation(summary = "创建或更新GitHub用户（内部）", description = "GitHub OAuth登录后创建或更新用户，供内部服务远程调用")
    @RequireInternalToken
    @DataSync(resource = SyncResource.USER, changeType = SyncChangeType.INSERT, description = "创建或更新GitHub用户后同步图谱与数仓")
    @ApiLog("内部创建或更新GitHub用户")
    public Mono<Result<UserVO>> findOrCreateGithubUser(@Valid @RequestBody GithubUserInternalDTO dto) {
        return userService.findOrCreateGithubUser(dto)
            .map(user -> {
                UserVO vo = BeanUtil.copyProperties(user, UserVO.class);
                return Result.success(vo);
            });
    }

    /**
     * GET /users/{id}/is-admin 内部接口，判断指定用户是否为管理员并返回布尔结果
     */
    @GetMapping("/{id}/is-admin")
    @Operation(summary = "判断用户是否为管理员（内部）", description = "根据用户ID判断是否为管理员，供内部服务远程调用")
    @RequireInternalToken
    @ApiLog("内部判断管理员")
    public Mono<Result<Boolean>> isAdminUser(@PathVariable Long id) {
        return userService.isAdminUser(id)
            .map(Result::success);
    }

    /**
     * GET /users/neo4j-sync 内部接口，按 updatedAfter 增量返回用户表数据供 FastAPI 同步 Neo4j
     */
    @GetMapping("/neo4j-sync")
    @Operation(summary = "获取用户表数据用于Neo4j同步（内部）", description = "获取用户表数据，支持增量同步，供FastAPI同步Neo4j使用")
    @RequireInternalToken
    @ApiLog("内部获取Neo4j同步用户数据")
    public Mono<Result<List<UserSyncVO>>> getNeo4jSyncUsers(
        @RequestParam(required = false) String updatedAfter) {
        return userService.getNeo4jSyncUsers(updatedAfter).map(Result::success);
    }

}
