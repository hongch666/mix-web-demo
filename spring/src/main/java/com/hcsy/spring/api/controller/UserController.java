package com.hcsy.spring.api.controller;

import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.api.service.EmailVerificationService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.common.utils.JwtUtil;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.common.utils.PasswordEncryptor;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.UserCreateDTO;
import com.hcsy.spring.entity.dto.UserQueryDTO;
import com.hcsy.spring.entity.dto.UserRegisterDTO;
import com.hcsy.spring.entity.dto.UserUpdateDTO;
import com.hcsy.spring.entity.dto.EmailLoginDTO;
import com.hcsy.spring.entity.dto.ResetPasswordDTO;
import com.hcsy.spring.entity.po.Result;
import com.hcsy.spring.entity.po.User;
import com.hcsy.spring.entity.vo.UserVO;

import cn.hutool.core.bean.BeanUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.*;
import org.springframework.cache.annotation.CacheConfig;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Caching;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@CacheConfig(cacheNames = "user")
@Tag(name = "用户模块", description = "用户相关接口")
public class UserController {
    private final UserService userService;
    private final TokenService tokenService;
    private final RedisUtil redisUtil;
    private final JwtUtil jwtUtil;
    private final SimpleLogger logger;
    private final EmailVerificationService emailVerificationService;
    private final PasswordEncryptor passwordEncryptor;

    @GetMapping()
    @Operation(summary = "获取用户信息", description = "分页获取用户信息列表，并支持用户名模糊查询，实时返回用户登录状态和设备数")
    @ApiLog("获取用户信息")
    public Result listUsers(@ModelAttribute UserQueryDTO queryDTO) {
        Map<String, Object> data = userService.listUsersWithFilter(
                queryDTO.getPage(),
                queryDTO.getSize(),
                queryDTO.getUsername());
        return Result.success(data);
    }

    @GetMapping("/all")
    @Operation(summary = "获取所有用户", description = "获取所有用户列表（不分页），结果会被缓存")
    @Cacheable(value = "userPage", key = "'all-users'")
    @ApiLog("获取所有用户")
    public Result getAllUsers() {
        Map<String, Object> data = userService.getAllUsers(null);
        return Result.success(data);
    }

    @PostMapping
    @Operation(summary = "新增用户", description = "创建新用户，如果不传密码则使用默认密码 123456")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", key = "'all-users'")
    })
    @ApiLog("新增用户")
    public Result addUser(@Valid @RequestBody UserCreateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        user.setRole("user");
        // 密码使用 DTO 中的默认值 "123456"，在 service 层加密
        userService.saveUserAndStatus(user);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", key = "'all-users'")
    })
    @ApiLog("删除用户")
    public Result deleteUser(@PathVariable Long id) {
        userService.deleteUserAndStatusById(id);
        return Result.success();
    }

    @DeleteMapping("/batch/{ids}")
    @Operation(summary = "批量删除用户", description = "根据id数组批量删除用户，多个id用英文逗号分隔")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", key = "'all-users'")
    })
    @ApiLog("批量删除用户")
    public Result deleteUsers(@PathVariable String ids) {
        List<Long> idList = Arrays.stream(ids.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::valueOf)
                .toList();
        userService.deleteUsersAndStatusByIds(idList);
        return Result.success();
    }

    @GetMapping("/{id}")
    @Operation(summary = "查询用户", description = "根据id查询用户，返回用户信息及其登录状态和设备数")
    @ApiLog("查询用户")
    public Result getUserById(@PathVariable Long id) {
        User user = userService.getById(id);
        if (user == null) {
            return Result.error("用户不存在");
        }

        // 转换为 UserVO
        UserVO userVO = BeanUtil.copyProperties(user, UserVO.class);

        // 从 Redis 查询登录状态和在线设备数
        String status = redisUtil.get("user:status:" + id);
        userVO.setLoginStatus("1".equals(status) ? 1 : 0);
        userVO.setOnlineDeviceCount(tokenService.getUserOnlineDeviceCount(id));

        return Result.success(userVO);
    }

    @PutMapping
    @Operation(summary = "修改用户", description = "通过请求体修改用户信息")
    @RequirePermission(roles = { "admin" }, allowSelf = true, targetUserIdParam = "userDto")
    @Caching(evict = {
            @CacheEvict(value = "userPage", key = "'all-users'")
    })
    @ApiLog("修改用户")
    public Result updateUser(@Valid @RequestBody UserUpdateDTO userDto) {
        // 获取原用户信息
        User existingUser = userService.getById(userDto.getId());
        if (existingUser == null) {
            return Result.error("用户不存在");
        }

        User user = BeanUtil.copyProperties(userDto, User.class);

        // 如果前端没有提供密码（为默认值"123456"），则保留原密码
        // 只有当前端明确提供了不同的密码时才更新
        if ("123456".equals(userDto.getPassword())) {
            user.setPassword(existingUser.getPassword());
        } else if (userDto.getPassword() != null && !userDto.getPassword().isEmpty()) {
            // 新密码需要加密
            user.setPassword(passwordEncryptor.encryptPassword(userDto.getPassword()));
        }

        userService.updateById(user);
        return Result.success();
    }

    @PutMapping("/status/{id}")
    @Operation(summary = "修改用户状态", description = "根据用户ID修改用户状态（存储在Redis中）")
    @RequirePermission(roles = { "admin" }, allowSelf = true)
    @Caching(evict = {
            @CacheEvict(value = "userPage", key = "'all-users'")
    })
    @ApiLog("修改用户状态")
    public Result updateUserStatus(@PathVariable Long id, @RequestParam String status) {
        String key = "user:status:" + id;
        redisUtil.set(key, status); // 设置为永久保存
        return Result.success();
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "根据用户名和密码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog("用户登录")
    public Result login(@RequestBody LoginDTO loginDTO) {
        User user = userService.findByUsername(loginDTO.getName());
        if (user == null || !passwordEncryptor.matchPassword(loginDTO.getPassword(), user.getPassword())) {
            return Result.error("用户名或密码错误");
        }

        // 1. 生成 JWT Token
        String token = jwtUtil.generateToken(user.getId(), user.getName());

        // 2. 保存 Token 到 Redis（包括标记用户在线）
        tokenService.saveToken(user.getId(), token);

        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("userId", user.getId());
        data.put("username", user.getName());
        // 3. 返回当前登录设备数
        data.put("onlineDeviceCount", tokenService.getUserOnlineDeviceCount(user.getId()));

        return Result.success(data);
    }

    @PostMapping("/email-login")
    @Operation(summary = "邮箱验证码登录", description = "通过邮箱和验证码进行登录，成功后返回JWT令牌，Token保存到Redis")
    @ApiLog("邮箱验证码登录")
    public Result emailLogin(@Valid @RequestBody EmailLoginDTO emailLoginDTO) {
        try {
            // 1. 验证邮箱验证码
            if (!emailVerificationService.verifyCode(emailLoginDTO.getEmail(), emailLoginDTO.getVerificationCode())) {
                return Result.error("邮箱验证码无效或已过期");
            }

            // 2. 查询用户是否存在
            User user = userService.findByEmail(emailLoginDTO.getEmail());
            if (user == null) {
                return Result.error("用户不存在，请先注册");
            }

            // 3. 生成 JWT Token
            String token = jwtUtil.generateToken(user.getId(), user.getName());

            // 4. 保存 Token 到 Redis（包括标记用户在线）
            tokenService.saveToken(user.getId(), token);

            Map<String, Object> data = new HashMap<>();
            data.put("token", token);
            data.put("userId", user.getId());
            data.put("username", user.getName());
            // 返回当前登录设备数
            data.put("onlineDeviceCount", tokenService.getUserOnlineDeviceCount(user.getId()));

            return Result.success(data);
        } catch (Exception e) {
            logger.error("邮箱验证码登录失败: " + e.getMessage());
            return Result.error("邮箱验证码登录失败");
        }
    }

    @PostMapping("/logout/{id}")
    @Operation(summary = "用户登出", description = "用户登出，将 Token 从 Redis 移除")
    @ApiLog("用户登出")
    public Result logout(@PathVariable Long id, @RequestHeader("Authorization") String authHeader) {
        try {
            // 从请求头中提取 Token（通常格式为 "Bearer token"）
            String token = authHeader.replace("Bearer ", "");
            // 从 Redis 移除 Token
            tokenService.removeToken(id, token);
            return Result.success();
        } catch (Exception e) {
            logger.error("登出失败: " + e.getMessage());
            return Result.error("登出失败");
        }
    }

    /**
     * 管理员手动下线用户
     */
    @PostMapping("/force-logout/{userId}")
    @Operation(summary = "手动下线用户", description = "管理员操作：将指定用户的所有登录会话强制下线")
    @RequirePermission(roles = { "admin" })
    @ApiLog("手动下线用户")
    public Result forceLogoutUser(@PathVariable Long userId) {
        try {
            // 验证用户是否存在
            User user = userService.getById(userId);
            if (user == null) {
                return Result.error("用户不存在");
            }

            // 执行下线操作
            tokenService.forceLogoutUser(userId);
            return Result.success();
        } catch (Exception e) {
            logger.error("手动下线用户失败: " + e.getMessage());
            return Result.error("手动下线用户失败");
        }
    }

    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "注册新用户，需要提供邮箱验证码")
    @ApiLog("用户注册")
    @Caching(evict = {
            @CacheEvict(value = "userPage", key = "'all-users'")
    })
    public Result registerUser(@Valid @RequestBody UserRegisterDTO registerDto) {
        // 1. 检查邮箱是否已被注册
        User existingUser = userService.findByEmail(registerDto.getEmail());
        if (existingUser != null) {
            return Result.error("邮箱已被注册");
        }

        // 2. 验证邮箱验证码
        if (!emailVerificationService.verifyCode(registerDto.getEmail(), registerDto.getVerificationCode())) {
            return Result.error("邮箱验证码无效或已过期");
        }

        // 3. 创建用户并加密密码
        User user = BeanUtil.copyProperties(registerDto, User.class);
        user.setRole("user");
        user.setPassword(passwordEncryptor.encryptPassword(user.getPassword()));
        userService.saveUserAndStatus(user);

        // 4. 标记邮箱已验证
        emailVerificationService.markEmailAsVerified(registerDto.getEmail());

        return Result.success("注册成功");
    }

    @PostMapping("/email/send")
    @Operation(summary = "发送邮箱验证码", description = "向指定邮箱发送验证码，支持注册(register)和登录(login)两种场景")
    @ApiLog("发送邮箱验证码")
    public Result sendVerificationCode(@RequestParam String email,
            @RequestParam(defaultValue = "register") String type) {
        try {
            // 1. 验证邮箱格式
            if (email == null || !email.matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
                return Result.error("邮箱格式不正确");
            }

            // 2. 根据类型验证邮箱状态
            User existingUser = userService.findByEmail(email);

            if ("register".equals(type)) {
                // 注册场景：邮箱不能已被注册
                if (existingUser != null) {
                    return Result.error("邮箱已被注册");
                }
            } else if ("login".equals(type) || "reset".equals(type)) {
                // 登录场景/重置密码场景：邮箱必须已被注册
                if (existingUser == null) {
                    return Result.error("邮箱未注册，请先注册");
                }
            } else {
                return Result.error("不支持的类型，请使用 register、login 或 reset");
            }

            // 3. 发送验证码
            emailVerificationService.sendVerificationCode(email);

            return Result.success("验证码已发送");
        } catch (Exception e) {
            logger.error("发送验证码异常: " + e.getMessage());
            return Result.error("发送验证码异常：" + e.getMessage());
        }
    }

    @PostMapping("/reset-password")
    @Operation(summary = "通过邮箱验证码重置密码", description = "用户通过邮箱验证码验证身份后重置密码")
    @ApiLog("重置密码")
    public Result resetPassword(@Valid @RequestBody ResetPasswordDTO resetPasswordDTO) {
        try {
            // 1. 验证邮箱验证码
            if (!emailVerificationService.verifyCode(resetPasswordDTO.getEmail(),
                    resetPasswordDTO.getVerificationCode())) {
                return Result.error("邮箱验证码无效或已过期");
            }

            // 2. 查询用户是否存在
            User user = userService.findByEmail(resetPasswordDTO.getEmail());
            if (user == null) {
                return Result.error("用户不存在");
            }

            // 3. 加密新密码后更新
            user.setPassword(passwordEncryptor.encryptPassword(resetPasswordDTO.getNewPassword()));
            userService.updateById(user);

            return Result.success();
        } catch (Exception e) {
            logger.error("重置密码失败: " + e.getMessage());
            return Result.error("重置密码失败");
        }
    }

    @PostMapping("/admin/reset-all-passwords")
    @Operation(summary = "管理员重置所有用户密码", description = "管理员操作：将所有用户密码重置为默认密码 123456")
    @RequirePermission(roles = { "admin" })
    @ApiLog("重置所有用户密码")
    public Result resetAllPasswords() {
        try {
            // 获取所有用户
            List<User> allUsers = userService.list();

            if (allUsers == null || allUsers.isEmpty()) {
                return Result.error("没有用户可重置");
            }

            // 重置所有用户密码为加密后的 123456
            final String defaultPassword = passwordEncryptor.encryptPassword("123456");
            allUsers.forEach(user -> user.setPassword(defaultPassword));
            userService.updateBatchById(allUsers);

            return Result.success();
        } catch (Exception e) {
            logger.error("重置所有用户密码失败: " + e.getMessage());
            return Result.error("重置所有用户密码失败");
        }
    }

    @PostMapping("/admin/reset-password/{userId}")
    @Operation(summary = "管理员重置指定用户密码", description = "管理员操作：将指定用户ID的密码重置为默认密码 123456")
    @RequirePermission(roles = { "admin" })
    @ApiLog("重置指定用户密码")
    public Result resetUserPassword(@PathVariable Long userId) {
        try {
            // 查询用户是否存在
            User user = userService.getById(userId);
            if (user == null) {
                return Result.error("用户不存在");
            }

            // 重置密码为加密后的 123456
            final String defaultPassword = passwordEncryptor.encryptPassword("123456");
            user.setPassword(defaultPassword);
            userService.updateById(user);

            return Result.success();
        } catch (Exception e) {
            logger.error("重置用户密码失败: " + e.getMessage());
            return Result.error("重置用户密码失败");
        }
    }
}
