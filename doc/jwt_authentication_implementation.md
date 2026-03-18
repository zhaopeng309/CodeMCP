# JWT 认证系统实现文档

## 概述

本文档详细介绍了 CodeMCP 项目中实现的 JWT（JSON Web Token）认证系统。该系统提供了完整的用户认证、授权和令牌管理功能，同时保持向后兼容性，支持原有的 `demo-token` 认证方式。

## 设计原则

1. **永不过期令牌**：根据用户要求，JWT 令牌不设置过期时间，一旦创建永不过期
2. **令牌撤销机制**：通过数据库记录实现令牌的主动撤销
3. **向后兼容**：支持原有的 `demo-token` 认证方式
4. **安全性**：使用 bcrypt 密码哈希和 HS256 JWT 签名算法
5. **生产就绪**：包含完整的用户管理、密码重置、令牌撤销等功能

## 系统架构

### 组件概览

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  认证 API 端点   │    │   JWT 工具模块   │    │   用户模型层    │
│  /auth/*        │◄──►│  create_token()  │◄──►│  User          │
│  - login        │    │  verify_token()  │    │  RevokedToken  │
│  - register     │    │  revoke_token()  │    └─────────────────┘
│  - logout       │    └─────────────────┘              ▲
│  - me           │              ▲                      │
└─────────────────┘              │                      │
         ▲                       │                      │
         │                       │                      │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FastAPI 依赖项  │    │   密码工具模块   │    │   数据库层      │
│  verify_token() │◄──►│  hash_password() │◄──►│  SQLAlchemy    │
│  get_current_user│    │  verify_password()│    │  AsyncSession  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 数据流

1. **用户登录**：用户名密码 → 密码验证 → JWT 生成 → 返回令牌
2. **API 访问**：Bearer 令牌 → JWT 验证 → 用户信息提取 → 权限检查
3. **令牌撤销**：令牌标识 → 数据库记录 → 后续验证失败

## 配置说明

### 环境变量

在 `.env` 文件中添加以下配置：

```bash
# JWT 配置
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# 默认管理员用户（首次初始化时创建）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
```

### 配置类

`src/codemcp/config.py` 中新增的配置字段：

```python
class Settings(BaseSettings):
    # ... 原有配置 ...
    
    # JWT 配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 签名密钥，生产环境必须修改"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT 签名算法"
    )
    
    # 管理员用户配置
    admin_username: str = Field(
        default="admin",
        description="默认管理员用户名"
    )
    admin_password: str = Field(
        default="admin123",
        description="默认管理员密码（首次启动后应立即修改）"
    )
    admin_email: str = Field(
        default="admin@example.com",
        description="默认管理员邮箱"
    )
```

## API 端点

### 认证相关端点

#### 1. 用户登录
- **端点**: `POST /auth/login`
- **请求体**:
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
- **响应**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

#### 2. 用户注册
- **端点**: `POST /auth/register`
- **请求体**:
  ```json
  {
    "username": "newuser",
    "email": "user@example.com",
    "password": "SecurePass123",
    "confirm_password": "SecurePass123"
  }
  ```

#### 3. 获取当前用户信息
- **端点**: `GET /auth/me`
- **认证**: Bearer 令牌
- **响应**: 当前用户的详细信息

#### 4. 更新用户信息
- **端点**: `PUT /auth/me`
- **认证**: Bearer 令牌
- **功能**: 更新邮箱或密码

#### 5. 用户登出
- **端点**: `POST /auth/logout`
- **认证**: Bearer 令牌
- **功能**: 撤销当前令牌

#### 6. 撤销所有令牌
- **端点**: `POST /auth/logout/all`
- **认证**: Bearer 令牌
- **功能**: 撤销用户的所有令牌

### 原有 API 的兼容性

所有原有 API 端点（如 `/tasks/*`）仍然支持两种认证方式：

1. **JWT 令牌**: `Authorization: Bearer <jwt-token>`
2. **旧版 demo-token**: `Authorization: Bearer demo-token`

## 数据库模型

### User 模型

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### RevokedToken 模型

```python
class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    token_id = Column(String(255), unique=True, nullable=False, index=True)  # JWT 的 jti 字段
    user_id = Column(String(255), nullable=False, index=True)  # 用户ID
    reason = Column(String(255), nullable=True)  # 撤销原因
    revoked_at = Column(DateTime, default=datetime.utcnow)
```

## 工具模块

### JWT 工具 (`src/codemcp/utils/jwt.py`)

#### 主要函数

1. **`create_token(user_id, username, email, is_superuser)`**
   - 创建永不过期的 JWT 令牌
   - 包含用户信息和唯一的 JWT ID (jti)

2. **`verify_token(token)`**
   - 验证 JWT 令牌的有效性
   - 检查令牌是否被撤销
   - 返回解码后的 payload

3. **`revoke_token(token, reason)`**
   - 撤销指定的 JWT 令牌
   - 将令牌 ID 记录到数据库

4. **`revoke_all_user_tokens(user_id, reason)`**
   - 撤销用户的所有令牌

### 密码工具 (`src/codemcp/utils/password.py`)

1. **`get_password_hash(password)`**
   - 使用 bcrypt 算法哈希密码

2. **`verify_password(plain_password, hashed_password)`**
   - 验证密码是否匹配哈希值

3. **`is_password_strong(password)`**
   - 检查密码强度（长度、数字、字母）

## 依赖注入

### 认证依赖 (`src/codemcp/api/dependencies.py`)

#### 1. `verify_token(credentials)`
- 验证令牌（兼容 JWT 和 demo-token）
- 返回令牌 payload

#### 2. `get_current_user(payload, db)`
- 获取当前用户对象
- 检查用户是否存在和是否激活

#### 3. `require_admin(user)`
- 要求管理员权限
- 检查用户是否为超级用户

#### 4. `authenticate_user(username, password, db)`
- 验证用户凭据
- 用于登录功能

### 依赖组合

```python
# 公共依赖（不需要认证）
PublicDeps = {
    "db": get_db,
    "settings": get_settings,
}

# 受保护依赖（需要认证）
ProtectedDeps = {
    **PublicDeps,
    "current_user": get_current_user,
}

# 管理员依赖
AdminDeps = {
    **ProtectedDeps,
    "admin_user": require_admin,
}
```

## 初始化和管理

### 初始化管理员用户

首次部署时需要创建默认管理员用户：

```bash
# 运行初始化脚本
python scripts/init_admin.py

# 列出所有用户
python scripts/init_admin.py list
```

### 数据库迁移

系统使用 SQLAlchemy 的 `create_all()` 方法自动创建表。如果需要 Alembic 迁移，可以扩展现有迁移系统。

## 使用示例

### 1. 获取 JWT 令牌

```bash
# 使用 curl 登录
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 响应示例
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. 使用 JWT 访问受保护 API

```bash
# 使用 JWT 访问 tasks API
curl -X GET http://localhost:8000/tasks/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 仍然可以使用旧的 demo-token
curl -X GET http://localhost:8000/tasks/ \
  -H "Authorization: Bearer demo-token"
```

### 3. 用户管理操作

```bash
# 获取当前用户信息
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <your-token>"

# 更新密码
curl -X PUT http://localhost:8000/auth/me \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "NewSecurePass123",
    "current_password": "admin123"
  }'

# 登出（撤销当前令牌）
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <your-token>"
```

## 安全注意事项

### 1. 生产环境配置
- **必须**修改 `JWT_SECRET_KEY`，使用强随机字符串
- **建议**定期轮换 JWT 密钥
- **必须**修改默认管理员密码

### 2. 令牌管理
- 令牌永不过期，需要主动撤销
- 敏感操作后建议撤销相关令牌
- 用户注销或密码更改时应撤销所有令牌

### 3. 密码策略
- 默认要求密码至少8位，包含数字和字母
- 使用 bcrypt 算法，自动加盐
- 建议实施更严格的密码策略

### 4. 速率限制
- 建议对登录端点实施速率限制
- 防止暴力破解攻击

## 故障排除

### 常见问题

1. **"无效的认证凭证" 错误**
   - 检查令牌格式是否正确
   - 验证令牌是否被撤销
   - 确认用户账户是否激活

2. **密码验证失败**
   - 检查密码哈希算法是否一致
   - 确认数据库中的哈希值格式正确

3. **数据库连接问题**
   - 检查数据库 URL 配置
   - 确认数据库表已创建

4. **bcrypt 版本错误**
   - 这是 passlib 的警告，不影响功能
   - 可以忽略或升级 bcrypt 库

### 调试建议

1. 启用调试日志查看详细错误信息
2. 检查数据库中的用户和令牌记录
3. 使用测试脚本验证各个组件功能

## 扩展和定制

### 添加新用户字段

1. 在 `User` 模型中添加新字段
2. 更新 `UserResponse` Pydantic 模型
3. 修改注册和更新端点

### 实现角色系统

1. 创建 `Role` 模型和用户-角色关联表
2. 在 JWT payload 中添加角色信息
3. 创建基于角色的权限检查依赖

### 添加 OAuth2 支持

1. 集成 `fastapi.security.OAuth2PasswordBearer`
2. 实现 OAuth2 提供商接口
3. 添加社交登录端点

### 实现令牌刷新机制

虽然当前设计使用永不过期令牌，但可以添加刷新机制：
1. 创建短期访问令牌和长期刷新令牌
2. 实现令牌刷新端点
3. 自动撤销旧的访问令牌

## 总结

本 JWT 认证系统提供了完整、安全、可扩展的认证解决方案，同时保持了与现有系统的兼容性。系统设计遵循了最佳安全实践，并提供了丰富的管理功能，适合生产环境使用。

关键特性：
- ✅ 永不过期 JWT 令牌（按用户要求）
- ✅ 令牌撤销机制
- ✅ 向后兼容 `demo-token`
- ✅ 完整的用户管理 API
- ✅ 密码哈希和强度检查
- ✅ 管理员权限控制
- ✅ 生产就绪配置

通过本系统，CodeMCP 项目具备了企业级的认证和授权能力，为后续的功能扩展奠定了坚实基础。