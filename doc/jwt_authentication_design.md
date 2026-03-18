# JWT 认证架构设计

## 1. 概述

为 CodeMCP 设计一个基于 JWT (JSON Web Token) 的生产环境认证系统，替换当前的简单令牌认证机制。根据要求，令牌一旦设置就永不过期，除非主动更新。

## 2. 设计目标

1. **安全性**: 使用行业标准的 JWT 认证
2. **永不过期**: 令牌没有过期时间，除非主动撤销或更新
3. **可扩展性**: 支持多用户、角色和权限
4. **向后兼容**: 保持现有 API 接口不变
5. **易于集成**: 提供清晰的文档和示例
6. **生产就绪**: 支持密钥轮换、令牌撤销等生产特性

## 3. 架构组件

### 3.1 JWT 配置
- **算法**: HS256 (HMAC with SHA-256)
- **令牌类型**: 单一长期令牌（永不过期）
- **撤销机制**: 通过令牌黑名单或数据库状态管理

### 3.2 用户模型
扩展现有数据模型，添加用户表：
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE revoked_tokens (
    id UUID PRIMARY KEY,
    token_id VARCHAR(255) UNIQUE NOT NULL,  -- JWT 的 jti (JWT ID)
    user_id UUID REFERENCES users(id),
    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(255)
);
```

### 3.3 认证流程
1. 用户通过 `/auth/login` 端点登录，获取长期有效的 JWT 令牌
2. 客户端在后续请求的 `Authorization: Bearer <token>` 头中携带令牌
3. 令牌永不过期，但可以通过以下方式撤销：
   - 用户主动登出 (`/auth/logout`)
   - 管理员撤销用户令牌
   - 安全事件（如密钥泄露）
4. 需要新令牌时重新登录

## 4. API 端点设计

### 4.1 认证端点
```
POST   /auth/login      # 用户登录，获取长期令牌
POST   /auth/logout     # 用户登出，撤销当前令牌
POST   /auth/register   # 用户注册（可选）
GET    /auth/me         # 获取当前用户信息
POST   /auth/revoke     # 管理员：撤销指定用户的令牌
GET    /auth/tokens     # 管理员：查看活跃令牌
```

### 4.2 令牌格式
**JWT Payload**:
```json
{
  "sub": "user_id",
  "username": "username",
  "email": "user@example.com",
  "is_superuser": false,
  "iat": 1672531200,  // 签发时间
  "jti": "unique-token-id",  // JWT ID，用于撤销
  "type": "access"
}
```

**注意**: 没有 `exp` (过期时间) 字段，因为令牌永不过期。

## 5. 依赖项

需要添加以下 Python 包：
```toml
# pyproject.toml
[dependencies]
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
```

## 6. 配置管理

### 6.1 环境变量
在 `.env` 文件中添加：
```bash
# JWT 配置
SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256

# 初始管理员账户（可选）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
```

### 6.2 配置类
更新 `src/codemcp/config.py`：
```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # JWT 配置
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="JWT 签名密钥"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT 算法")
    
    # 初始管理员账户
    admin_username: str = Field(default="admin", description="初始管理员用户名")
    admin_password: str = Field(default="admin123", description="初始管理员密码")
    admin_email: str = Field(default="admin@example.com", description="初始管理员邮箱")
```

## 7. 核心实现

### 7.1 JWT 工具模块
```python
# src/codemcp/utils/jwt.py
import uuid
from datetime import datetime
from jose import JWTError, jwt
from ..config import settings

def create_token(user_id: str, username: str, email: str, is_superuser: bool = False) -> str:
    """创建永不过期的 JWT 令牌"""
    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "is_superuser": is_superuser,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),  # 唯一标识符，用于撤销
        "type": "access"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> dict:
    """验证 JWT 令牌"""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise AuthenticationError("无效的令牌")
```

### 7.2 令牌撤销机制
```python
# src/codemcp/utils/token_manager.py
from ..database.session import get_db_session
from ..models.user import RevokedToken

class TokenManager:
    """令牌管理器，处理令牌撤销"""
    
    async def revoke_token(self, token_id: str, user_id: str, reason: str = None):
        """撤销令牌"""
        async with get_db_session() as db:
            revoked_token = RevokedToken(
                token_id=token_id,
                user_id=user_id,
                reason=reason
            )
            db.add(revoked_token)
            await db.commit()
    
    async def is_token_revoked(self, token_id: str) -> bool:
        """检查令牌是否被撤销"""
        async with get_db_session() as db:
            result = await db.execute(
                select(RevokedToken).where(RevokedToken.token_id == token_id)
            )
            return result.scalar_one_or_none() is not None
```

## 8. 安全考虑

### 8.1 永不过期令牌的安全策略
1. **强密钥管理**: 使用至少 8 字符的密钥
2. **令牌撤销机制**: 完善的令牌撤销系统
3. **密钥轮换策略**: 定期轮换 JWT 密钥，使所有旧令牌失效
4. **监控和审计**: 记录所有令牌创建和撤销事件

### 8.2 密钥轮换流程
当需要轮换密钥时：
1. 生成新密钥并更新 `SECRET_KEY` 环境变量
2. 重启服务，使所有旧令牌失效
3. 通知用户重新登录获取新令牌
4. 可选：提供过渡期，支持新旧密钥验证

### 8.3 其他安全措施
- HTTPS 强制
- CORS 配置
- 输入验证和清理
- 安全头设置
- 速率限制防止暴力破解

## 9. 向后兼容性

### 9.1 迁移策略
1. 阶段 1: 实现新认证系统，与旧 `demo-token` 系统并行
2. 阶段 2: 更新客户端使用新 JWT 认证
3. 阶段 3: 停用旧 `demo-token` 系统

### 9.2 兼容模式
在 `dependencies.py` 中提供向后兼容：
```python
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="缺少认证凭证")
    
    token = credentials.credentials
    
    # 首先尝试 JWT 验证
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        # 检查令牌是否被撤销
        if await token_manager.is_token_revoked(payload.get("jti")):
            raise HTTPException(status_code=401, detail="令牌已被撤销")
        return payload["sub"]
    except JWTError:
        # 回退到旧版 demo-token 验证（迁移期间）
        if token == "demo-token":
            return "demo-user"
        raise HTTPException(status_code=401, detail="无效的认证凭证")
```

## 10. 运维考虑

### 10.1 密钥管理
- 生产环境使用环境变量或密钥管理服务
- 不同环境（开发、测试、生产）使用不同密钥
- 密钥备份策略

### 10.2 监控
- 认证失败日志
- 令牌创建和撤销统计
- 异常访问模式检测

### 10.3 灾难恢复
- 密钥备份和恢复流程
- 用户数据备份
- 紧急访问流程（如管理员令牌）

## 11. 测试策略

### 11.1 单元测试
- JWT 创建和验证测试
- 令牌撤销测试
- 密码哈希测试

### 11.2 集成测试
- 认证端点测试
- 受保护端点测试
- 令牌撤销流程测试

### 11.3 安全测试
- 无效令牌测试
- 撤销令牌测试
- 权限测试

## 12. 文档

### 12.1 开发者文档
- API 认证指南
- 令牌获取和使用示例
- 错误处理指南

### 12.2 运维文档
- 配置说明
- 密钥轮换流程
- 故障排除

### 12.3 用户文档
- 认证流程说明
- 客户端集成指南
- 常见问题解答