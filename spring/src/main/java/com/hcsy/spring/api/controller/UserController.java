package com.hcsy.spring.api.controller;

import java.util.Arrays;
import java.util.List;

import org.springdoc.core.annotations.ParameterObject;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.api.service.ImageCaptchaService;
import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.utils.Result;
import com.hcsy.spring.common.utils.UserContext;
import com.hcsy.spring.core.annotation.ApiLog;
import com.hcsy.spring.core.annotation.Neo4jSync;
import com.hcsy.spring.core.annotation.RequireInternalToken;
import com.hcsy.spring.core.annotation.RequirePermission;
import com.hcsy.spring.entity.dto.EmailCodeSendDTO;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.GithubTokenExchangeDTO;
import com.hcsy.spring.entity.dto.GithubTokenTicketCreateDTO;
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
import com.hcsy.spring.entity.vo.UserVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@Tag(name = "用户模块", description = "用户管理功能相关API，包括用户注册、登录、信息管理、验证码等")
public class UserController {
    private final UserService userService;
    private final TokenService tokenService;
    private final EmailVerificationService emailVerificationService;
    private final ImageCaptchaService imageCaptchaService;

    @GetMapping()
    @Operation(summary = "获取用户信息", description = "分页获取用户信息列表，并支持用户名模糊查询，实时返回用户登录状态和设备数")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "query", paramNames = { "page", "size",
            "username" })
    @ApiLog("获取用户信息")
    public Mono<Result<UserListVO>> listUsers(@ParameterObject @ModelAttribute UserQueryDTO queryDTO) {
        return userService.listUsersWithFilter(queryDTO.getPage(), queryDTO.getSize(), queryDTO.getUsername())
                .map(Result::success);
    }

    @GetMapping("/all")
    @Operation(summary = "获取所有用户", description = "获取所有用户列表（不分页）")
    @ApiLog("获取所有用户")
    public Mono<Result<UserListVO>> getAllUsers() {
        return userService.getAllUsers(null).map(Result::success);
    }

    @GetMapping("/ai")
    @Operation(summary = "获取所有AI用户", description = "获取 role 为 ai 的用户列表，不分页")
    @ApiLog("获取所有AI用户")
    public Mono<Result<UserListVO>> getAllAiUsers() {
        return userService.getAllAiUsers().map(Result::success);
    }

    @PostMapping
    @Operation(summary = "新增用户", description = "创建新用户，如果不传密码则使用配置中的默认密码")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "body", paramNames = { "id" })
    @ApiLog("新增用户")
    public Mono<Result<Void>> addUser(@Valid @RequestBody UserCreateDTO userDto) {
        return userService.createUser(userDto).thenReturn(Result.<Void>success());
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "path_single", paramNames = { "id" })
    @ApiLog("删除用户")
    public Mono<Result<Void>> deleteUser(@PathVariable Long id) {
        return userService.deleteUserAndStatusById(id).thenReturn(Result.<Void>success());
    }

    @SuppressWarnings("null")
    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除用户", description = "根据id数组批量删除用户，多个id用英文逗号分隔")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "path_single", paramNames = { "ids" })
    @ApiLog("批量删除用户")
    public Mono<Result<Void>> deleteUsers(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        return userService.deleteUsersAndStatusByIds(idList).thenReturn(Result.<Void>success());
    }

    @GetMapping("/{id}")
    @Operation(summary = "查询用户", description = "根据id查询用户，返回用户信息及其登录状态和设备数")
    @ApiLog("查询用户")
    public Mono<Result<UserVO>> getUserById(@PathVariable Long id) {
        return userService.getById(id)
                .flatMap(user -> Mono.zip(
                        userService.getUserLoginStatus(id),
                        tokenService.getUserOnlineDeviceCount(id))
                        .map(status -> {
                            UserVO userVO = BeanUtil.copyProperties(user, UserVO.class);
                            userVO.setLoginStatus(status.getT1());
                            userVO.setOnlineDeviceCount(status.getT2());
                            return Result.success(userVO);
                        }))
                .defaultIfEmpty(Result.<UserVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

    @PutMapping
    @Operation(summary = "修改用户", description = "通过请求体修改用户信息")
    @RequirePermission(roles = {
            "admin" }, allowSelf = true, businessType = "user", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_UPDATE)
    @ApiLog("修改用户")
    public Mono<Result<Void>> updateUser(@Valid @RequestBody UserUpdateDTO userDto) {
        return userService.updateUserInfo(userDto).thenReturn(Result.<Void>success());
    }

    @PutMapping("/status/{id}")
    @Operation(summary = "修改用户状态", description = "根据用户ID修改用户状态（存储在Redis中）")
    @RequirePermission(roles = {
            "admin" }, allowSelf = true, businessType = "user", paramSource = "path_single", paramNames = { "id" })
    @ApiLog("修改用户状态")
    public Mono<Result<Void>> updateUserStatus(@PathVariable Long id, @RequestParam String status) {
        return userService.updateUserStatus(id, status).thenReturn(Result.<Void>success());
    }

    @GetMapping("/captcha")
    @Operation(summary = "获取图形验证码", description = "生成图形验证码，返回验证码ID和base64图片数据，验证码缓存到Redis并在5分钟后过期")
    @ApiLog("获取图形验证码")
    public Mono<Result<ImageCaptchaVO>> getImageCaptcha() {
        return imageCaptchaService.createCaptcha().map(Result::success);
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "根据用户名和密码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog("用户登录")
    public Mono<Result<UserLoginVO>> login(@Valid @RequestBody LoginDTO loginDTO) {
        return userService.login(loginDTO).map(Result::success);
    }

    @PostMapping("/email-login")
    @Operation(summary = "邮箱验证码登录", description = "通过邮箱和验证码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog("邮箱验证码登录")
    public Mono<Result<UserLoginVO>> emailLogin(@Valid @RequestBody EmailLoginDTO emailLoginDTO) {
        return userService.emailLogin(emailLoginDTO).map(Result::success);
    }

    @PostMapping("/github/token-ticket")
    @Operation(summary = "生成 GitHub 登录票据", description = "在 GitHub 回调成功后生成本站登录票据")
    @RequireInternalToken
    @ApiLog("生成 GitHub 登录票据")
    public Mono<Result<GithubTokenTicketVO>> createGithubTokenTicket(
            @Valid @RequestBody GithubTokenTicketCreateDTO dto) {
        return userService.createGithubTokenTicket(dto).map(Result::success);
    }

    @PostMapping("/github/token")
    @Operation(summary = "获取 GitHub 登录 Token", description = "前端使用一次性 ticket 换取本站登录 token，成功后立即删除 ticket")
    @ApiLog("获取 GitHub 登录 Token")
    public Mono<Result<UserLoginVO>> exchangeGithubToken(@Valid @RequestBody GithubTokenExchangeDTO dto) {
        return userService.exchangeGithubTokenTicket(dto).map(Result::success);
    }

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

    @PostMapping("/token/refresh")
    @Operation(summary = "刷新 Token", description = "使用 refresh token 刷新 access token 和 refresh token，支持 token 轮换")
    @ApiLog("刷新 Token")
    public Mono<Result<TokenRefreshVO>> refreshToken(@Valid @RequestBody RefreshTokenDTO refreshTokenDTO) {
        return tokenService.refreshToken(refreshTokenDTO.getRefreshToken()).map(Result::success);
    }

    /**
     * 管理员手动下线用户
     */
    @PostMapping("/force-logout/{user_id}")
    @Operation(summary = "手动下线用户", description = "管理员操作：将指定用户的所有登录会话强制下线")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "path_single", paramNames = {
            "user_id" })
    @ApiLog("手动下线用户")
    public Mono<Result<Void>> forceLogoutUser(@PathVariable("user_id") Long userId) {
        return userService.getById(userId)
                .flatMap(user -> tokenService.forceLogoutUser(userId).thenReturn(Result.<Void>success()))
                .defaultIfEmpty(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
    }

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

            return tokenService.removeOtherSessions(userId, token)
                    .flatMap(removed -> tokenService.getUserOnlineDeviceCount(userId)
                            .map(remaining -> Result.success(KickOtherDevicesVO.builder()
                                    .userId(userId)
                                    .removedSessionCount(removed)
                                    .onlineDeviceCount(remaining)
                                    .build())));
        });
    }

    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "注册新用户，需要提供邮箱验证码")
    @ApiLog("用户注册")
    public Mono<Result<Void>> registerUser(@Valid @RequestBody UserRegisterDTO registerDto) {
        return userService.registerUser(registerDto).thenReturn(Result.<Void>success());
    }

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
        if (resolvedEmail == null || !resolvedEmail.matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
            return Mono.just(Result.error(HttpCode.UNPROCESSABLE_ENTITY, Messages.EMAIL));
        }
        if (!"register".equals(resolvedType) && !"login".equals(resolvedType) && !"reset".equals(resolvedType)) {
            return Mono.just(Result.error(HttpCode.BAD_REQUEST, Messages.VERIFY_CODE_UNSUPPORT));
        }

        String finalEmail = resolvedEmail;
        String finalType = resolvedType;
        return userService.findByEmail(finalEmail).hasElement().flatMap(exists -> {
            if ("register".equals(finalType) && exists) {
                return Mono.just(Result.<Void>error(HttpCode.CONFLICT, Messages.EMAIL_REGISTER));
            }
            if (!"register".equals(finalType) && !exists) {
                return Mono.just(Result.<Void>error(HttpCode.NOT_FOUND, Messages.EMAIL_UNREGISTER));
            }
            return emailVerificationService.sendVerificationCode(finalEmail, finalType)
                    .thenReturn(Result.<Void>success());
        });
    }

    @PostMapping("/reset-password")
    @Operation(summary = "通过邮箱验证码重置密码", description = "用户通过邮箱验证码验证身份后重置密码")
    @ApiLog("重置密码")
    public Mono<Result<Void>> resetPassword(@Valid @RequestBody ResetPasswordDTO resetPasswordDTO) {
        return userService.resetPassword(resetPasswordDTO).thenReturn(Result.<Void>success());
    }

    @PostMapping("/admin/reset-all-passwords")
    @Operation(summary = "管理员重置所有用户密码", description = "管理员操作：将所有用户密码重置为配置中的重置密码")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "body", paramNames = { "id" })
    @ApiLog("重置所有用户密码")
    public Mono<Result<Void>> resetAllPasswords() {
        return userService.resetAllPasswords().thenReturn(Result.<Void>success());
    }

    @PostMapping("/admin/reset-password/{user_id}")
    @Operation(summary = "管理员重置指定用户密码", description = "管理员操作：将指定用户ID的密码重置为配置中的重置密码")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "path_single", paramNames = {
            "user_id" })
    @ApiLog("重置指定用户密码")
    public Mono<Result<Void>> resetUserPassword(@PathVariable("user_id") Long userId) {
        return userService.resetUserPassword(userId).thenReturn(Result.<Void>success());
    }
}
