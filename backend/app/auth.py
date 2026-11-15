import os
import hmac
import json
import time
import base64
import hashlib
from typing import Literal, Optional
from fastapi import Header, HTTPException, status, Depends

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-enterprise-support-key-2026")
RoleType = Literal["customer", "admin"]


def hash_password(password: str, salt: str = "support_salt_v1") -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


# Pre-hashed credential store (Email -> Account Record)
# Customer Passwords: "password123" | Admin Password: "adminpassword"
USER_CREDENTIALS = {
    "alice.j@verizon.net": {
        "user_id": "cust_001",
        "name": "Alice Johnson",
        "role": "customer",
        "password_hash": hash_password("password123"),
    },
    "bob.smith@enterprise.io": {
        "user_id": "cust_002",
        "name": "Bob Smith",
        "role": "customer",
        "password_hash": hash_password("password123"),
    },
    "priya.nair@techcorp.in": {
        "user_id": "cust_003",
        "name": "Priya Nair",
        "role": "customer",
        "password_hash": hash_password("password123"),
    },
    "mvance@outlook.com": {
        "user_id": "cust_004",
        "name": "Marcus Vance",
        "role": "customer",
        "password_hash": hash_password("password123"),
    },
    "elena.r@designstudio.co": {
        "user_id": "cust_005",
        "name": "Elena Rostova",
        "role": "customer",
        "password_hash": hash_password("password123"),
    },
    "dkim@cloudscale.dev": {
        "user_id": "cust_006",
        "name": "David Kim",
        "role": "customer",
        "password_hash": hash_password("password123"),
    },
    "admin@support.io": {
        "user_id": "mgr_01",
        "name": "Operations Manager",
        "role": "admin",
        "password_hash": hash_password("adminpassword"),
    },
}


def create_access_token(user_id: str, email: str, role: RoleType, name: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": name,
        "exp": int(time.time()) + 86400,  # 24-hour expiration
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{b64_payload}.{signature}"


def decode_access_token(token: str) -> dict:
    try:
        b64_payload, signature = token.split(".")
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid token signature")

        padding = "=" * (-len(b64_payload) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(b64_payload + padding).decode("utf-8")
        )
        if payload.get("exp", 0) < int(time.time()):
            raise ValueError("Token expired")
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc


class AuthContext:
    def __init__(self, role: RoleType, user_id: str, email: str, name: str):
        self.role = role
        self.user_id = user_id
        self.email = email
        self.name = name


def get_auth_context(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> AuthContext:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authentication token. Please sign in.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    return AuthContext(
        role=payload["role"],
        user_id=payload["sub"],
        email=payload["email"],
        name=payload["name"],
    )


def require_admin(auth: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if auth.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin role required.",
        )
    return auth