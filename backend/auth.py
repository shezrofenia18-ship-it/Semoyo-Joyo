"""JWT auth helpers + FastAPI dependencies."""
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me")
JWT_ALG = "HS256"
TOKEN_DAYS = 30


def normalize_username(full_name: str) -> str:
    """'SPPG Dapur Melati ' -> 'sppg-dapur-melati' (Nama Lengkap menjadi ID login)."""
    s = full_name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "pelanggan"


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("62"):
        digits = "0" + digits[2:]
    return digits


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: Optional[str]) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def create_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "role": user.role,
        "name": user.full_name,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesi berakhir, silakan masuk kembali")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token tidak valid")


async def _user_from_header(authorization: Optional[str], db: AsyncSession) -> Optional[User]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    data = decode_token(token)
    res = await db.execute(select(User).where(User.id == data.get("sub")))
    return res.scalar_one_or_none()


async def get_current_user(authorization: Optional[str] = Header(default=None), db: AsyncSession = Depends(get_db)) -> User:
    user = await _user_from_header(authorization, db)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Silakan masuk terlebih dahulu")
    return user


async def get_optional_user(authorization: Optional[str] = Header(default=None), db: AsyncSession = Depends(get_db)) -> Optional[User]:
    try:
        return await _user_from_header(authorization, db)
    except HTTPException:
        return None


STAFF_ROLES = ("admin", "owner")


def is_owner(user: User) -> bool:
    return user.role == "owner"


async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """Staff (admin ATAU owner) boleh mengakses panel admin."""
    if user.role not in STAFF_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Akses khusus admin")
    return user


async def get_owner_user(user: User = Depends(get_current_user)) -> User:
    """Hanya Owner: hapus data, keuangan/modal, audit log."""
    if user.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Aksi ini hanya dapat dilakukan oleh Owner")
    return user


async def user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """Untuk SSE (EventSource tidak bisa mengirim header Authorization)."""
    data = decode_token(token)
    res = await db.execute(select(User).where(User.id == data.get("sub")))
    return res.scalar_one_or_none()
