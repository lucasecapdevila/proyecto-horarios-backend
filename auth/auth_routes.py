from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal
from auth.crud_user import get_user, create_user, authenticate_user
from auth.auth_utils import create_access_token, decode_access_token
from models import RoleEnum
from schemas import UserRegister, UserOut, Token, UserLogin
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["Autenticación"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = get_user(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    from models import RoleEnum
    new_user = create_user(db, user.username, user.userpassword, RoleEnum.admin)
    return new_user

@router.post("/login", response_model=Token)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    user_db = authenticate_user(db, user.username, user.userpassword)
    if not user_db:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    access_token = create_access_token({"sub": user_db.username, "role": user_db.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_current_user(token: str, db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    username = payload.get("sub")
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user