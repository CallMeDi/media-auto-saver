# -*- coding: utf-8 -*-
# /usr/bin/env python3

from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# 中文: 创建密码哈希上下文, 使用 bcrypt 算法
# English: Create password hashing context using bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 中文: JWT 算法
# English: JWT Algorithm
ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    中文: 创建 JWT 访问令牌。
    English: Create a JWT access token.

    参数 / Parameters:
        subject: 令牌的主题 (例如用户 ID 或用户名) / The subject of the token (e.g., user ID or username).
        expires_delta: 令牌过期时间增量, 如果为 None, 使用配置中的默认值 / Token expiration delta, if None, use default from settings.

    返回 / Returns:
        str: 生成的 JWT 令牌 / The generated JWT token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    # 中文: 确保 SECRET_KEY 已设置
    # English: Ensure SECRET_KEY is set
    if not settings.SECRET_KEY:
        raise ValueError("SECRET_KEY not configured in settings")
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    中文: 验证明文密码与哈希密码是否匹配。
    English: Verify if the plain password matches the hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    中文: 获取密码的哈希值。
    English: Get the hash of a password.
    """
    return pwd_context.hash(password)

def decode_token(token: str) -> Optional[str]:
    """
    中文: 解码 JWT 令牌并获取主题 (通常是用户 ID)。
    English: Decode JWT token and get the subject (usually user ID).

    返回 / Returns:
        Optional[str]: 令牌的主题, 如果令牌无效或过期则返回 None / The subject of the token, or None if the token is invalid or expired.
    """
    try:
        if not settings.SECRET_KEY:
             raise ValueError("SECRET_KEY not configured in settings")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
        return subject
    except JWTError:
        # 中文: 令牌无效或过期 / Token is invalid or expired
        return None
