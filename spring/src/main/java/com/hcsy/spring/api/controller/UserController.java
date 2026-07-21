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
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.constants.HttpCode;
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
import com.hcsy.spring.entity.po.User;
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
        return Mono.deferContextual(ctx -> {
            UserListVO data = userService.listUsersWithFilter(
                    queryDTO.getPage(),
                    queryDTO.getSize(),
                    queryDTO.getUsername());
            return Mono.just(Result.success(data));
        });
    }

    @GetMapping("/all")
    @Operation(summary = "获取所有用户", description = "获取所有用户列表（不分页）")
    @ApiLog("获取所有用户")
    public Mono<Result<UserListVO>> getAllUsers() {
        return Mono.deferContextual(ctx -> {
            UserListVO data = userService.getAllUsers(null);
            return Mono.just(Result.success(data));
        });
    }

    @GetMapping("/ai")
    @Operation(summary = "获取所有AI用户", description = "获取 role 为 ai 的用户列表，不分页")
    @ApiLog("获取所有AI用户")
    public Mono<Result<UserListVO>> getAllAiUsers() {
        return Mono.deferContextual(ctx -> {
            UserListVO data = userService.getAllAiUsers();
            return Mono.just(Result.success(data));
        });
    }

    @PostMapping
    @Operation(summary = "新增用户", description = "创建新用户，如果不传密码则使用配置中的默认密码")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "body", paramNames = { "id" })
    @ApiLog("新增用户")
    public Mono<Result<Void>> addUser(@Valid @RequestBody UserCreateDTO userDto) {
        return Mono.deferContextual(ctx -> {
            userService.createUser(userDto);
            return Mono.just(Result.<Void>success());
        });
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "path_single", paramNames = { "id" })
    @ApiLog("删除用户")
    public Mono<Result<Void>> deleteUser(@PathVariable Long id) {
        return Mono.deferContextual(ctx -> {
            userService.deleteUserAndStatusById(id);
            return Mono.just(Result.<Void>success());
        });
    }

    @SuppressWarnings("null")
    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除用户", description = "根据id数组批量删除用户，多个id用英文逗号分隔")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "path_single", paramNames = { "ids" })
    @ApiLog("批量删除用户")
    public Mono<Result<Void>> deleteUsers(@PathVariable String ids) {
        return Mono.deferContextual(ctx -> {
            List<Long> idList = Arrays.stream(ids.split(","))
                    .map(String::trim)
                    .filter(s -> !s.isEmpty())
                    .map(Long::valueOf)
                    .toList();
            userService.deleteUsersAndStatusByIds(idList);
            return Mono.just(Result.<Void>success());
        });
    }

    @GetMapping("/{id}")
    @Operation(summary = "查询用户", description = "根据id查询用户，返回用户信息及其登录状态和设备数")
    @ApiLog("查询用户")
    public Mono<Result<UserVO>> getUserById(@PathVariable Long id) {
        return Mono.deferContextual(ctx -> {
            User user = userService.getById(id);
            if (user == null) {
                return Mono.just(Result.<UserVO>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
            }

            // 转换为 UserVO
            UserVO userVO = BeanUtil.copyProperties(user, UserVO.class);

            // 从 Service 查询登录状态和在线设备数
            userVO.setLoginStatus(userService.getUserLoginStatus(id));
            userVO.setOnlineDeviceCount(tokenService.getUserOnlineDeviceCount(id));

            return Mono.just(Result.success(userVO));
        });
    }

    @PutMapping
    @Operation(summary = "修改用户", description = "通过请求体修改用户信息")
    @RequirePermission(roles = {
            "admin" }, allowSelf = true, businessType = "user", paramSource = "body", paramNames = { "id" })
    @Neo4jSync(description = Messages.NEO4J_SYNC_DESC_USER_UPDATE)
    @ApiLog("修改用户")
    public Mono<Result<Void>> updateUser(@Valid @RequestBody UserUpdateDTO userDto) {
        return Mono.deferContextual(ctx -> {
            userService.updateUserInfo(userDto);
            return Mono.just(Result.<Void>success());
        });
    }

    @PutMapping("/status/{id}")
    @Operation(summary = "修改用户状态", description = "根据用户ID修改用户状态（存储在Redis中）")
    @RequirePermission(roles = {
            "admin" }, allowSelf = true, businessType = "user", paramSource = "path_single", paramNames = { "id" })
    @ApiLog("修改用户状态")
    public Mono<Result<Void>> updateUserStatus(@PathVariable Long id, @RequestParam String status) {
        return Mono.deferContextual(ctx -> {
            userService.updateUserStatus(id, status);
            return Mono.just(Result.<Void>success());
        });
    }

    @GetMapping("/captcha")
    @Operation(summary = "获取图形验证码", description = "生成图形验证码，返回验证码ID和base64图片数据，验证码缓存到Redis并在5分钟后过期")
    @ApiLog("获取图形验证码")
    public Mono<Result<ImageCaptchaVO>> getImageCaptcha() {
        return Mono.deferContextual(ctx -> {
            ImageCaptchaVO captchaVO = imageCaptchaService.createCaptcha();
            return Mono.just(Result.success(captchaVO));
        });
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "根据用户名和密码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog("用户登录")
    public Mono<Result<UserLoginVO>> login(@Valid @RequestBody LoginDTO loginDTO) {
        return Mono.deferContextual(ctx -> {
            UserLoginVO loginVO = userService.login(loginDTO);
            return Mono.just(Result.success(loginVO));
        });
    }

    @PostMapping("/email-login")
    @Operation(summary = "邮箱验证码登录", description = "通过邮箱和验证码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog("邮箱验证码登录")
    public Mono<Result<UserLoginVO>> emailLogin(@Valid @RequestBody EmailLoginDTO emailLoginDTO) {
        return Mono.deferContextual(ctx -> {
            UserLoginVO loginVO = userService.emailLogin(emailLoginDTO);
            return Mono.just(Result.success(loginVO));
        });
    }

    @PostMapping("/github/token-ticket")
    @Operation(summary = "生成 GitHub 登录票据", description = "在 GitHub 回调成功后生成本站登录票据")
    @RequireInternalToken
    @ApiLog("生成 GitHub 登录票据")
    public Mono<Result<GithubTokenTicketVO>> createGithubTokenTicket(@Valid @RequestBody GithubTokenTicketCreateDTO dto) {
        return Mono.deferContextual(ctx -> {
            GithubTokenTicketVO ticketVO = userService.createGithubTokenTicket(dto);
            return Mono.just(Result.success(ticketVO));
        });
    }

    @PostMapping("/github/token")
    @Operation(summary = "获取 GitHub 登录 Token", description = "前端使用一次性 ticket 换取本站登录 token，成功后立即删除 ticket")
    @ApiLog("获取 GitHub 登录 Token")
    public Mono<Result<UserLoginVO>> exchangeGithubToken(@Valid @RequestBody GithubTokenExchangeDTO dto) {
        return Mono.deferContextual(ctx -> {
            UserLoginVO loginVO = userService.exchangeGithubTokenTicket(dto);
            return Mono.just(Result.success(loginVO));
        });
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
            tokenService.removeSessionByAccessToken(accessToken);
            return Mono.just(Result.<Void>success());
        });
    }

    @PostMapping("/token/refresh")
    @Operation(summary = "刷新 Token", description = "使用 refresh token 刷新 access token 和 refresh token，支持 token 轮换")
    @ApiLog("刷新 Token")
    public Mono<Result<TokenRefreshVO>> refreshToken(@Valid @RequestBody RefreshTokenDTO refreshTokenDTO) {
        return Mono.deferContextual(ctx -> {
            TokenRefreshVO tokenRefreshVO = tokenService.refreshToken(refreshTokenDTO.getRefreshToken());
            return Mono.just(Result.success(tokenRefreshVO));
        });
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
        return Mono.deferContextual(ctx -> {
            // 验证用户是否存在
            User user = userService.getById(userId);
            if (user == null) {
                return Mono.just(Result.<Void>error(HttpCode.NOT_FOUND, Messages.UNDEFINED_USER));
            }

            // 执行下线操作
            tokenService.forceLogoutUser(userId);
            return Mono.just(Result.<Void>success());
        });
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

            int removed = tokenService.removeOtherSessions(userId, token);
            long remaining = tokenService.getUserOnlineDeviceCount(userId);

            KickOtherDevicesVO vo = KickOtherDevicesVO.builder()
                    .userId(userId)
                    .removedSessionCount(removed)
                    .onlineDeviceCount(remaining)
                    .build();
            return Mono.just(Result.success(vo));
        });
    }

    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "注册新用户，需要提供邮箱验证码")
    @ApiLog("用户注册")
    public Mono<Result<Void>> registerUser(@Valid @RequestBody UserRegisterDTO registerDto) {
        return Mono.deferContextual(ctx -> {
            userService.registerUser(registerDto);
            return Mono.just(Result.<Void>success());
        });
    }

    @PostMapping("/email/send")
    @Operation(summary = "发送邮箱验证码", description = "向指定邮箱发送验证码，支持注册(register)和登录(login)两种场景")
    @ApiLog("发送邮箱验证码")
    public Mono<Result<Void>> sendVerificationCode(@RequestParam(required = false) String email,
            @RequestParam(required = false) String type,
            @RequestBody(required = false) EmailCodeSendDTO body) {
        return Mono.deferContextual(ctx -> {
            String finalEmail = email;
            String finalType = type;
            if (body != null) {
                if (finalEmail == null || finalEmail.isBlank()) {
                    finalEmail = body.getEmail();
                }
                if (finalType == null || finalType.isBlank()) {
                    finalType = body.getType();
                }
            }
            if (finalType == null || finalType.isBlank()) {
                finalType = "register";
            }

            // 1. 验证邮箱格式
            if (finalEmail == null || !finalEmail.matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
                return Mono.just(Result.<Void>error(HttpCode.UNPROCESSABLE_ENTITY, Messages.EMAIL));
            }

            // 2. 根据类型验证邮箱状态
            User existingUser = userService.findByEmail(finalEmail);

            if ("register".equals(finalType)) {
                // 注册场景：邮箱不能已被注册
                if (existingUser != null) {
                    return Mono.just(Result.<Void>error(HttpCode.CONFLICT, Messages.EMAIL_REGISTER));
                }
            } else if ("login".equals(finalType) || "reset".equals(finalType)) {
                // 登录场景/重置密码场景：邮箱必须已被注册
                if (existingUser == null) {
                    return Mono.just(Result.<Void>error(HttpCode.NOT_FOUND, Messages.EMAIL_UNREGISTER));
                }
            } else {
                return Mono.just(Result.<Void>error(HttpCode.BAD_REQUEST, Messages.VERIFY_CODE_UNSUPPORT));
            }

            // 3. 发送验证码
            emailVerificationService.sendVerificationCode(finalEmail, finalType);

            return Mono.just(Result.<Void>success());
        });
    }

    @PostMapping("/reset-password")
    @Operation(summary = "通过邮箱验证码重置密码", description = "用户通过邮箱验证码验证身份后重置密码")
    @ApiLog("重置密码")
    public Mono<Result<Void>> resetPassword(@Valid @RequestBody ResetPasswordDTO resetPasswordDTO) {
        return Mono.deferContextual(ctx -> {
            userService.resetPassword(resetPasswordDTO);
            return Mono.just(Result.<Void>success());
        });
    }

    @PostMapping("/admin/reset-all-passwords")
    @Operation(summary = "管理员重置所有用户密码", description = "管理员操作：将所有用户密码重置为配置中的重置密码")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "body", paramNames = { "id" })
    @ApiLog("重置所有用户密码")
    public Mono<Result<Void>> resetAllPasswords() {
        return Mono.deferContextual(ctx -> {
            userService.resetAllPasswords();
            return Mono.just(Result.<Void>success());
        });
    }

    @PostMapping("/admin/reset-password/{user_id}")
    @Operation(summary = "管理员重置指定用户密码", description = "管理员操作：将指定用户ID的密码重置为配置中的重置密码")
    @RequirePermission(roles = { "admin" }, businessType = "user", paramSource = "path_single", paramNames = {
            "user_id" })
    @ApiLog("重置指定用户密码")
    public Mono<Result<Void>> resetUserPassword(@PathVariable("user_id") Long userId) {
        return Mono.deferContextual(ctx -> {
            userService.resetUserPassword(userId);
            return Mono.just(Result.<Void>success());
        });
    }
}
