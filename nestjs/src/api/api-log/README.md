# ApiLog 模块使用指南

## 模块概述

ApiLog 模块用于记录系统中所有 API 的调用日志，包括请求信息、响应时间等。**该模块不提供直接的创建接口，而是通过 RabbitMQ 消息队列异步消费消息进行日志创建**，便于后续的审计、分析和调试。

## 功能特性

- ✅ **异步消费创建**：从消息队列异步消费日志创建消息
- ✅ **查询日志**：支持多条件过滤和分页查询
- ✅ **删除日志**：支持单条和批量删除
- ✅ **时间范围查询**：支持按创建时间范围查询
- ✅ **模糊搜索**：支持按用户名、API 路径、API 描述模糊搜索

## 目录结构

```
api-log/
├── schema/
│   └── api.log.schema.ts              # MongoDB Schema 定义
├── dto/
│   └── index.ts                        # DTO 定义
├── api.log.module.ts                   # 模块定义
├── api.log.service.ts                  # 业务逻辑服务
├── api.log.controller.ts               # 控制器（查询、删除）
├── api.log.consume.service.ts          # 消费者服务（消费创建消息）
└── README.md                          # 本文档
```

## 消息队列配置

### 队列名称

- **队列名**：`api-log-queue`
- **持久化**：true（重启后消息不丢失）
- **消息格式**：JSON

## 消息格式规范

### 创建 API 日志消息

消息队列中发送的 JSON 格式如下：

```json
{
  "user_id": 1,
  "username": "admin",
  "api_description": "获取用户信息",
  "api_path": "/api/users/1",
  "api_method": "GET",
  "query_params": {
    "page": 1,
    "size": 10
  },
  "path_params": {
    "id": "1"
  },
  "request_body": {
    "name": "test"
  },
  "response_time": 100
}
```

### 字段说明

| 字段            | 类型   | 必需 | 说明                                                        |
| --------------- | ------ | ---- | ----------------------------------------------------------- |
| user_id         | number | 是   | 用户 ID，如果为空默认为 -1                                  |
| username        | string | 是   | 用户名，如果为空默认为 "unknown"                            |
| api_description | string | 是   | API 描述，如果为空默认为空字符串                            |
| api_path        | string | 是   | API 路径（如 /api/users/1），如果为空默认为空字符串         |
| api_method      | string | 是   | API 方法（GET、POST、PUT、DELETE 等），如果为空默认为 "GET" |
| query_params    | object | 否   | 查询参数（任意 JSON 对象），可为 null 或不传                |
| path_params     | object | 否   | 路径参数（任意 JSON 对象），可为 null 或不传                |
| request_body    | object | 否   | 请求体（任意 JSON 对象），可为 null 或不传                  |
| response_time   | number | 是   | 响应时间（毫秒），如果为空默认为 0                          |

## API 接口文档

### 1. 查询 API 日志（分页）

**请求方式**：GET

**请求路径**：`/api-logs/list`

**查询参数**：

| 参数           | 类型   | 必需 | 说明                                  |
| -------------- | ------ | ---- | ------------------------------------- |
| userId         | string | 否   | 用户 ID                               |
| username       | string | 否   | 用户名（模糊搜索）                    |
| apiDescription | string | 否   | API 描述（模糊搜索）                  |
| apiPath        | string | 否   | API 路径（模糊搜索）                  |
| apiMethod      | string | 否   | API 方法（GET/POST/PUT/DELETE 等）    |
| startTime      | string | 否   | 开始时间（格式：yyyy-MM-dd HH:mm:ss） |
| endTime        | string | 否   | 结束时间（格式：yyyy-MM-dd HH:mm:ss） |
| page           | string | 否   | 页码，默认为 1                        |
| size           | string | 否   | 每页条数，默认为 10                   |

**请求示例**：

```bash
GET /api-logs/list?userId=1&apiMethod=GET&page=1&size=10
```

**响应示例**：

```json
{
  "total": 100,
  "list": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "userId": 1,
      "username": "admin",
      "apiDescription": "获取用户信息",
      "apiPath": "/api/users/1",
      "apiMethod": "GET",
      "queryParams": {
        "page": 1,
        "size": 10
      },
      "pathParams": {
        "id": "1"
      },
      "requestBody": null,
      "responseTime": 100,
      "createdAt": "2025-10-23 10:30:45",
      "updatedAt": "2025-10-23 10:30:45"
    }
  ]
}
```

---

### 2. 获取所有 API 日志

**请求方式**：GET

**请求路径**：`/api-logs/all`

**响应示例**：

```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "userId": 1,
    "username": "admin",
    "apiDescription": "获取用户信息",
    "apiPath": "/api/users/1",
    "apiMethod": "GET",
    "queryParams": null,
    "pathParams": null,
    "requestBody": null,
    "responseTime": 100,
    "createdAt": "2025-10-23 10:30:45",
    "updatedAt": "2025-10-23 10:30:45"
  }
]
```

---

### 3. 查询单条 API 日志

**请求方式**：GET

**请求路径**：`/api-logs/:id`

**路径参数**：

| 参数 | 说明    |
| ---- | ------- |
| id   | 日志 ID |

**请求示例**：

```bash
GET /api-logs/507f1f77bcf86cd799439011
```

**响应示例**：

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "userId": 1,
  "username": "admin",
  "apiDescription": "获取用户信息",
  "apiPath": "/api/users/1",
  "apiMethod": "GET",
  "queryParams": null,
  "pathParams": null,
  "requestBody": null,
  "responseTime": 100,
  "createdAt": "2025-10-23 10:30:45",
  "updatedAt": "2025-10-23 10:30:45"
}
```

---

### 4. 删除单条 API 日志

**请求方式**：DELETE

**请求路径**：`/api-logs/:id`

**路径参数**：

| 参数 | 说明    |
| ---- | ------- |
| id   | 日志 ID |

**请求示例**：

```bash
DELETE /api-logs/507f1f77bcf86cd799439011
```

**响应**：

```json
null
```

---

### 5. 批量删除 API 日志

**请求方式**：DELETE

**请求路径**：`/api-logs/batch/:ids`

**路径参数**：

| 参数 | 说明                                 |
| ---- | ------------------------------------ |
| ids  | 日志 ID 列表，多个 ID 用英文逗号分隔 |

**请求示例**：

```bash
DELETE /api-logs/batch/507f1f77bcf86cd799439011,507f1f77bcf86cd799439012,507f1f77bcf86cd799439013
```

**响应**：

```json
null
```

---

## 数据模型

### ApiLog Schema

```typescript
{
  userId: number,              // 用户ID
  username: string,            // 用户名
  apiDescription: string,      // API描述
  apiPath: string,             // API路径
  apiMethod: string,           // API方法（GET、POST等）
  queryParams?: object,        // 查询参数
  pathParams?: object,         // 路径参数
  requestBody?: object,        // 请求体
  responseTime: number,        // 响应时间（毫秒）
  createdAt?: Date,            // 创建时间（自动生成）
  updatedAt?: Date             // 更新时间（自动生成）
}
```

## RabbitMQ 消费处理

### 消费流程

1. 应用启动时，`ApiLogConsumerService` 会自动连接 RabbitMQ
2. 监听 `api-log-queue` 队列
3. 当队列中有新消息时，自动消费并处理
4. 提取消息中的字段，转换为 `CreateApiLogDto`
5. 将数据保存到 MongoDB

### 错误处理

- 如果消息字段缺失，使用默认值（如 user_id 缺失默认为 -1）
- 如果处理过程中发生错误，会记录到日志文件
- 消息处理失败后会抛出异常，消息不会被 ACK，会重新进入队列

## 消息队列消息示例

### 示例 1: 查询用户接口

```json
{
  "user_id": 1,
  "username": "admin",
  "api_description": "查询用户列表",
  "api_path": "/api/users",
  "api_method": "GET",
  "query_params": {
    "page": 1,
    "size": 10,
    "status": "active"
  },
  "path_params": null,
  "request_body": null,
  "response_time": 120
}
```

### 示例 2: 创建用户接口

```json
{
  "user_id": 2,
  "username": "operator",
  "api_description": "创建新用户",
  "api_path": "/api/users",
  "api_method": "POST",
  "query_params": null,
  "path_params": null,
  "request_body": {
    "name": "张三",
    "email": "zhangsan@example.com",
    "role": "user"
  },
  "response_time": 250
}
```

### 示例 3: 更新订单接口

```json
{
  "user_id": 3,
  "username": "sales",
  "api_description": "更新订单状态",
  "api_path": "/api/orders/12345",
  "api_method": "PUT",
  "query_params": null,
  "path_params": {
    "order_id": "12345"
  },
  "request_body": {
    "status": "shipped",
    "tracking_number": "SF123456789"
  },
  "response_time": 180
}
```

### 示例 4: 删除文章接口

```json
{
  "user_id": 1,
  "username": "admin",
  "api_description": "删除文章",
  "api_path": "/api/articles/999",
  "api_method": "DELETE",
  "query_params": null,
  "path_params": {
    "article_id": "999"
  },
  "request_body": null,
  "response_time": 95
}
```

### 示例 5: 最小化消息（使用默认值）

```json
{
  "user_id": 5,
  "username": "guest",
  "api_description": "获取配置",
  "api_path": "/api/config",
  "api_method": "GET",
  "response_time": 50
}
```

---

## 时区配置

模块默认使用 **Asia/Shanghai** 时区，所有返回的时间戳都会按此时区格式化。

如需修改时区，可在 `api.log.service.ts` 中修改 `TIMEZONE` 常量：

```typescript
const TIMEZONE = 'Asia/Shanghai'; // 修改此处
```

## 注意事项

1. **消息队列必须**：RabbitMQ 必须正常运行，否则应用启动会失败
2. **性能考虑**：大量日志写入可能影响性能，建议定期清理旧日志
3. **敏感信息**：避免在 `request_body` 中发送敏感信息（如密码等）
4. **响应时间**：以毫秒（ms）为单位记录
5. **时间查询**：时间范围查询需要提供完整的日期时间格式：`yyyy-MM-dd HH:mm:ss`
6. **消息字段**：使用 snake_case（下划线）命名，例如 `user_id`、`api_path` 等
7. **错误重试**：如果消息处理失败，会自动重新入队并重试

## 使用示例

### 在其他模块中记录日志

```typescript
import { RabbitMQService } from 'src/common/mq/mq.service';

@Injectable()
export class YourService {
  constructor(private readonly rabbitMQService: RabbitMQService) {}

  async someApiCall() {
    const startTime = Date.now();

    try {
      // 执行业务逻辑
      // ...

      const responseTime = Date.now() - startTime;

      // 发送日志消息到队列
      await this.rabbitMQService.sendToQueue('api-log-queue', {
        user_id: 1,
        username: 'admin',
        api_description: '获取用户信息',
        api_path: '/api/users/1',
        api_method: 'GET',
        query_params: { page: 1 },
        response_time: responseTime,
      });
    } catch (error) {
      // 错误处理
    }
  }
}
```

## 故障排除

| 问题             | 解决方案                               |
| ---------------- | -------------------------------------- |
| 消费者未启动     | 检查 RabbitMQ 连接是否正常             |
| 消息未被消费     | 检查队列名称是否为 `api-log-queue`     |
| 日志创建失败     | 查看日志文件中的错误信息，检查消息字段 |
| MongoDB 连接失败 | 检查 MongoDB 配置和连接状态            |
