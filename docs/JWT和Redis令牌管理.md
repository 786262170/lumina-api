# JWT Token 管理和 Redis 黑名单机制

## 问题：仅使用 JWT 的局限性

### JWT 的过期机制

JWT 本身**可以自动过期**，因为：
- JWT 包含 `exp`（expiration time）字段
- 验证时会自动检查是否过期
- 过期的 token 会被自动拒绝

**但是，JWT 有一个重要限制：**

⚠️ **一旦签发，在过期前无法主动撤销！**

### 问题场景

1. **用户登出**：用户点击登出，但 token 在过期前仍然有效
2. **安全事件**：token 泄露，需要立即撤销
3. **权限变更**：用户权限被修改，需要撤销旧 token
4. **多设备登录**：用户想踢出某个设备的登录

**仅使用 JWT 无法解决这些问题！**

---

## 解决方案：JWT + Redis 黑名单

### 架构设计

```
┌─────────────┐
│   用户登录   │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌─────────────┐
│  生成 JWT    │─────│  返回给用户   │
└─────────────┘      └─────────────┘
       │
       │ (可选：存储 token 到 Redis)
       │
       ▼
┌─────────────┐
│  Token 验证  │
└──────┬──────┘
       │
       ├─► 检查 JWT 签名和过期时间
       │
       ├─► 检查 Redis 黑名单
       │
       └─► 验证通过/拒绝
```

### 实现方式

#### 方式一：Token 黑名单（当前实现）

**优点：**
- ✅ 精确控制：可以撤销单个 token
- ✅ 简单高效：只存储被撤销的 token
- ✅ 自动清理：Redis TTL 自动删除过期 token

**缺点：**
- ⚠️ 需要 Redis（但可以降级到无 Redis 模式）

**实现：**

```python
# 登出时，将 token 加入黑名单
def logout(token: str):
    payload = verify_token(token)
    expires_in = payload["exp"] - current_time
    redis.setex(f"blacklist:token:{token_hash}", expires_in, "1")

# 验证时，检查黑名单
def verify_token(token: str):
    if is_token_blacklisted(token):
        return None  # Token 已被撤销
    # ... 继续验证 JWT
```

#### 方式二：存储所有 Token（不推荐）

**缺点：**
- ❌ 存储量大：需要存储所有活跃 token
- ❌ 性能问题：每次验证都要查询 Redis
- ❌ 失去 JWT 无状态的优势

---

## 当前实现

### 1. Redis 客户端 (`app/utils/redis_client.py`)

```python
def get_redis_client() -> Optional[redis.Redis]:
    """获取 Redis 客户端（单例模式）"""
    if not settings.redis_enabled:
        return None  # Redis 未启用时返回 None
    # ...
```

**特性：**
- ✅ 支持 Redis 未启用时的降级模式
- ✅ 单例模式，避免重复连接
- ✅ 自动处理连接错误

### 2. Token 黑名单 (`app/utils/jwt.py`)

#### 添加 token 到黑名单

```python
def add_token_to_blacklist(token: str, expires_in_seconds: int) -> bool:
    """
    将 token 加入黑名单
    
    Redis Key: blacklist:token:{token_hash}
    TTL: token 的剩余有效期
    """
    redis_client.setex(
        f"blacklist:token:{token_hash}",
        expires_in_seconds,
        "1"
    )
```

#### 检查 token 是否在黑名单

```python
def is_token_blacklisted(token: str) -> bool:
    """检查 token 是否在黑名单中"""
    return redis.exists(f"blacklist:token:{token_hash}") > 0
```

#### Token 验证（已集成黑名单检查）

```python
def verify_token(token: str) -> Optional[Dict]:
    # 1. 先检查黑名单
    if is_token_blacklisted(token):
        return None
    
    # 2. 验证 JWT 签名和过期时间
    payload = jwt.decode(token, ...)
    
    # 3. 检查用户级别的撤销（可选）
    if user_tokens_revoked(user_id):
        return None
    
    return payload
```

### 3. 登出接口 (`app/api/v1/auth.py`)

```python
@router.post("/auth/logout")
async def logout_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    current_user: User = Depends(get_current_user)
):
    """登出：将 token 加入黑名单"""
    token = credentials.credentials
    payload = verify_token(token)
    
    # 计算剩余有效期
    expires_in = payload["exp"] - current_time
    
    # 加入黑名单
    add_token_to_blacklist(token, expires_in)
    
    return {"success": True, "message": "登出成功"}
```

---

## 配置说明

### .env 配置

```env
# Redis 配置
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true  # 设置为 true 启用 Redis

# JWT 配置
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120  # Access token 2 小时
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30    # Refresh token 30 天
```

### 降级模式

如果 `REDIS_ENABLED=false` 或 Redis 不可用：

- ✅ 系统仍然可以运行
- ✅ JWT 过期机制仍然有效
- ⚠️ 但无法主动撤销 token（登出功能受限）

**建议：** 生产环境启用 Redis。

---

## JWT 过期 vs Redis 黑名单

### JWT 自动过期（无需 Redis）

```python
# JWT 包含过期时间
{
  "sub": "user_123",
  "exp": 1704067200,  # 过期时间戳
  "iat": 1704060000   # 签发时间
}

# 验证时自动检查
jwt.decode(token, ...)  # 如果过期，自动抛出异常
```

**适用场景：**
- ✅ 正常的 token 过期
- ✅ 不需要主动撤销
- ✅ 简单的无状态认证

### Redis 黑名单（需要 Redis）

```python
# 登出时加入黑名单
redis.setex("blacklist:token:abc123", 3600, "1")

# 验证时检查
if redis.exists("blacklist:token:abc123"):
    return None  # Token 已被撤销
```

**适用场景：**
- ✅ 用户主动登出
- ✅ 安全事件（token 泄露）
- ✅ 权限变更需要立即生效
- ✅ 多设备管理

---

## 性能考虑

### Redis 查询性能

- **单次查询**：O(1) 时间复杂度
- **延迟**：通常 < 1ms（本地 Redis）
- **影响**：每次 token 验证增加一次 Redis 查询

### 优化建议

1. **使用连接池**：复用 Redis 连接
2. **批量检查**：如果有多 token，可以批量查询
3. **本地缓存**：可以添加本地缓存（但要注意一致性）

---

## 安全考虑

### 1. Token Hash

当前实现使用 token 的前 32 个字符作为 hash：

```python
token_hash = token[:32]  # 使用前 32 字符
```

**更安全的做法（可选）：**

```python
import hashlib
token_hash = hashlib.sha256(token.encode()).hexdigest()
```

### 2. 用户级别撤销

除了单个 token 黑名单，还支持用户级别的撤销：

```python
def revoke_user_tokens(user_id: str):
    """撤销用户的所有 token"""
    redis.set(f"blacklist:user:{user_id}", current_timestamp)
    
# 验证时检查
if token_issued_before_revocation(token, user_id):
    return None
```

### 3. 错误处理

- **Redis 不可用**：降级到无黑名单模式（fail open）
- **连接错误**：允许 token（保证可用性）
- **生产环境**：应该监控 Redis 状态

---

## 使用示例

### 1. 启用 Redis

```env
# .env
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

### 2. 启动 Redis

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### 3. 测试登出

```bash
# 1. 登录获取 token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phoneNumber": "13812345678", "verificationCode": "123456"}'

# 响应: {"token": "eyJ...", ...}

# 2. 使用 token 访问受保护接口
curl -X GET http://localhost:8000/v1/user/profile \
  -H "Authorization: Bearer eyJ..."

# 3. 登出
curl -X POST http://localhost:8000/v1/auth/logout \
  -H "Authorization: Bearer eyJ..."

# 4. 再次使用 token（应该被拒绝）
curl -X GET http://localhost:8000/v1/user/profile \
  -H "Authorization: Bearer eyJ..."
# 响应: 401 Unauthorized
```

---

## 总结

### JWT 过期机制

- ✅ **可以自动过期**：通过 `exp` 字段
- ✅ **无需存储**：JWT 是无状态的
- ❌ **无法主动撤销**：一旦签发，在过期前无法撤销

### Redis 黑名单的作用

- ✅ **主动撤销**：可以立即撤销 token
- ✅ **登出功能**：实现真正的登出
- ✅ **安全控制**：处理 token 泄露等安全事件
- ✅ **自动清理**：Redis TTL 自动删除过期 token

### 最佳实践

1. **开发环境**：可以禁用 Redis（`REDIS_ENABLED=false`）
2. **生产环境**：**必须启用 Redis**（`REDIS_ENABLED=true`）
3. **监控**：监控 Redis 连接状态
4. **降级策略**：Redis 不可用时，系统仍可运行（但登出功能受限）

---

## 相关文件

- `app/utils/jwt.py` - JWT 工具函数（包含黑名单检查）
- `app/utils/redis_client.py` - Redis 客户端
- `app/api/v1/auth.py` - 登出接口
- `app/dependencies.py` - Token 验证依赖

