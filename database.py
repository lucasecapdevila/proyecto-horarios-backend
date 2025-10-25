import os
from sqlalchemy import create_engine, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# SQLite URL de la base de datos local
LOCAL_DATABASE_URL = "sqlite:///./horarios.db" 

# Obtener la URL de la base de datos desde una variable de entorno o usar la local por defecto
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", LOCAL_DATABASE_URL)

# Verificar si estamos en producción (PostgreSQL) o en desarrollo (SQLite)
IS_PRODUCTION = SQLALCHEMY_DATABASE_URL.startswith("postgresql://")

# Configurar el motor de la base de datos
engine = None
if IS_PRODUCTION:
  # Configuración para PostgreSQL
  engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
  # Configuración para SQLite
  engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()