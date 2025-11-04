import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, RoleEnum

load_dotenv()

SECRET_KEY = os.getenv("SECRET_JWT")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 120))

if not SECRET_KEY:
    raise ValueError("SECRET_JWT no está configurada en las variables de entorno")

# Funciones de hashing de contraseñas usando bcrypt directamente
def hash_password(password: str) -> str:
    # Encode la contraseña como bytes, genera el salt y hashea
    password_bytes = password.encode('utf-8')
    # Truncar la contraseña a 72 bytes (límite de bcrypt)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Encode ambos como bytes y verifica
    password_bytes = plain_password.encode('utf-8')
    # Truncar la contraseña a 72 bytes (límite de bcrypt)
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Punto central del OAuth2 estándar: los tokens deben ir en header Authorization: Bearer ...
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependencia: obtiene el usuario autenticado (levanta error si token es inválido o no hay user)
def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_dep)) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user

# Dependencia: retorna user si autenticado, o None si no lo está (para casos opcionales, rara vez se usa para este proyecto pero queda listo)
def get_current_user_optional(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db_dep)) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    return user

# Dependencia: SOLO deja pasar a usuarios administrador, y da error 403 si no lo es
def get_admin_user(current_user: User = Depends(get_current_user_from_token)) -> User:
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return current_user