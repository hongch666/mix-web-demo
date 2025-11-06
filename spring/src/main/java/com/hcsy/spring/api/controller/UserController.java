package com.hcsy.spring.api.controller;

import com.hcsy.spring.api.service.UserService;
import com.hcsy.spring.api.service.TokenService;
import com.hcsy.spring.common.annotation.ApiLog;
import com.hcsy.spring.common.annotation.RequirePermission;
import com.hcsy.spring.common.utils.JwtUtil;
import com.hcsy.spring.common.utils.RedisUtil;
import com.hcsy.spring.common.utils.SimpleLogger;
import com.hcsy.spring.entity.dto.LoginDTO;
import com.hcsy.spring.entity.dto.UserCreateDTO;
import com.hcsy.spring.entity.dto.UserQueryDTO;
import com.hcsy.spring.entity.dto.UserUpdateDTO;
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
    private final com.hcsy.spring.common.mq.RabbitMQService rabbitMQService;

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
    @Operation(summary = "新增用户", description = "通过请求体创建用户信息")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true)
    })
    @ApiLog("新增用户")
    public Result addUser(@Valid @RequestBody UserCreateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        user.setRole("user");
        userService.saveUserAndStatus(user);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除用户", description = "根据id删除用户")
    @RequirePermission(roles = { "admin" })
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", key = "#id")
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
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", allEntries = true)
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
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", key = "#userDto.id")
    })
    @ApiLog("修改用户")
    public Result updateUser(@Valid @RequestBody UserUpdateDTO userDto) {
        User user = BeanUtil.copyProperties(userDto, User.class);
        userService.updateById(user);
        return Result.success();
    }

    @PutMapping("/status/{id}")
    @Operation(summary = "修改用户状态", description = "根据用户ID修改用户状态（存储在Redis中）")
    @RequirePermission(roles = { "admin" }, allowSelf = true)
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true),
            @CacheEvict(value = "userById", key = "#id")
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
        long startTime = System.currentTimeMillis();
        logger.info("POST /users/login: " + "用户登录\nLoginDTO: %s", loginDTO);

        User user = userService.findByUsername(loginDTO.getName());
        if (user == null || !user.getPassword().equals(loginDTO.getPassword())) {
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
        // 新增：返回当前登录设备数
        data.put("onlineDeviceCount", tokenService.getUserOnlineDeviceCount(user.getId()));

        // 发送 API 日志到 RabbitMQ
        long responseTime = System.currentTimeMillis() - startTime;
        sendApiLogToQueue(user.getId(), user.getName(), "POST", "/users/login", "用户登录",
                null, null, loginDTO, responseTime);

        return Result.success(data);
    }

    @PostMapping("/logout/{id}")
    @Operation(summary = "用户登出", description = "用户登出，将 Token 从 Redis 移除")
    @Caching(evict = {
            @CacheEvict(value = "userById", key = "#id"),
            @CacheEvict(value = "userPage", allEntries = true)
    })
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
    @Operation(summary = "用户注册", description = "注册新用户")
    @Caching(evict = {
            @CacheEvict(value = "userPage", allEntries = true)
    })
    public Result registerUser(@Valid @RequestBody UserCreateDTO userDto) {
        long startTime = System.currentTimeMillis();
        logger.info("POST /users/register: " + "用户注册\nUserCreateDTO: %s", userDto);

        User user = BeanUtil.copyProperties(userDto, User.class);
        user.setRole("user");
        userService.saveUserAndStatus(user);

        // 发送 API 日志到 RabbitMQ（使用注册成功后的用户信息）
        long responseTime = System.currentTimeMillis() - startTime;
        sendApiLogToQueue(user.getId(), user.getName(), "POST", "/users/register", "用户注册",
                null, null, userDto, responseTime);

        return Result.success();
    }

    /**
     * 发送 API 日志到 RabbitMQ
     * 
     * @param userId       用户ID
     * @param username     用户名
     * @param method       HTTP方法
     * @param path         API路径
     * @param description  API描述
     * @param queryParams  查询参数
     * @param pathParams   路径参数
     * @param requestBody  请求体
     * @param responseTime 响应时间（毫秒）
     */
    private void sendApiLogToQueue(Long userId, String username, String method, String path,
            String description, Map<String, String> queryParams,
            Map<String, String> pathParams, Object requestBody, long responseTime) {
        try {
            // 构建 API 日志消息（统一格式：snake_case）
            Map<String, Object> apiLogMessage = new HashMap<>();
            apiLogMessage.put("user_id", userId);
            apiLogMessage.put("username", username);
            apiLogMessage.put("api_description", description);
            apiLogMessage.put("api_path", path);
            apiLogMessage.put("api_method", method);
            apiLogMessage.put("query_params", queryParams);
            apiLogMessage.put("path_params", pathParams);
            apiLogMessage.put("request_body", requestBody);
            apiLogMessage.put("response_time", responseTime);

            // 发送到 RabbitMQ
            rabbitMQService.sendMessage("api-log-queue", apiLogMessage);
            logger.info("API 日志已发送到队列");
        } catch (Exception e) {
            logger.error("发送 API 日志到队列失败: " + e.getMessage());
        }
    }

}
