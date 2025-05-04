# -*- coding: utf-8 -*-
# /usr/bin/env python3

from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """
    中文: API 返回的令牌模型
    English: Token model returned by the API
    """
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """
    中文: JWT 令牌内部的载荷模型
    English: Payload model inside the JWT token
    """
    sub: Optional[str] = None # subject (通常是 user_id) / subject (usually user_id)
