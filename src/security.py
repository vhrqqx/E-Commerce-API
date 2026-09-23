from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError
import models
import uuid
from db.databases import get_db
import redis
from db.redis_config import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-jwt-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_TIME_DURATION = 15 # token co hieu luc trong 60 phut
REFRESH_TOKEN_EXPIRE_DAYS = 7 # token cho refresh token (7 ngay)
oauth2scheme = OAuth2PasswordBearer(tokenUrl="login")

def hash_pwd(password: str) -> str:
    """Băm mật khẩu plain-text thành chuỗi hash an toàn."""
    return pwd_context.hash(password)

def verify_pwd(plain_password: str, hased_password: str) -> bool:
    """So khớp mật khẩu nhập vào với chuỗi hash trong database (dùng cho lúc Login)."""
    return pwd_context.verify(plain_password, hased_password)

def create_access_token(user_id: int) -> str:
    expire_in = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_TIME_DURATION)
    to_encode = {
        "sub" : str(user_id),
        "type" : "access",
        "jti" : str(uuid.uuid4()),
        "exp" : expire_in
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub" : str(user_id),
        "type" : "refresh",
        "jti" : (uuid.uuid4()),
        "exp" : expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=[ALGORITHM])

def get_current_user(token: str = Depends(oauth2scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token này đã bị hủy bỏ do người dùng đã đăng xuất!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti: str = payload.get("jti")
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception
        # Kiem tra blacklist redis
        if redis_client:
            try:
                is_blacklisted = redis_client.get(f"blacklist:{jti}")
                if is_blacklisted:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token này đã bị thu hồi do bạn đã đăng xuất!"
                    )
            except redis.RedisError as e:
                print(f"Loi kiem tra Redis Blacklist: {e}")
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quyền truy cập bị từ chối! Hành động này chỉ dành cho Quản trị viên (Admin)."
        )
    return current_user