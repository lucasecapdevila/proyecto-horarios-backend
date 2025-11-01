from sqlalchemy.orm import Session
from models import User
from auth.auth_utils import hash_password, verify_password

def get_user(db: Session, username: str):
  return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, role):
  hashed_password = hash_password(password)
  db_user = User(username=username, hashed_password=hashed_password, role=role)
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

def authenticate_user(db: Session, username: str, password: str):
  user = get_user(db, username)
  if not user or not verify_password(password, user.userpassword):
    return None
  return user