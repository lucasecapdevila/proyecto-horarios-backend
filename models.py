from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base
import enum

class Linea(Base):
  __tablename__ = "lineas"

  id = Column(Integer, primary_key=True)
  nombre = Column(String, unique=True)
  recorridos = relationship("Recorrido", back_populates="linea")

class Recorrido(Base):
  __tablename__ = "recorridos"

  id = Column(Integer, primary_key=True)
  origen = Column(String)
  destino = Column(String)
  linea_id = Column(Integer, ForeignKey("lineas.id"))
  linea = relationship("Linea", back_populates="recorridos")
  horarios = relationship("Horario", back_populates="recorrido")

class Horario(Base):
  __tablename__ = "horarios"

  id = Column(Integer, primary_key=True)
  tipo_dia = Column(String)
  hora_salida = Column(String)
  hora_llegada = Column(String)
  directo = Column(Boolean, default=False)
  recorrido_id = Column(Integer, ForeignKey("recorridos.id"))
  recorrido = relationship("Recorrido", back_populates="horarios")

class RoleEnum(enum.Enum):
  admin = "Administrador"
  user = "Usuario"

class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  username = Column(String, unique=True, nullable=False)
  userpassword = Column(String, nullable=False)
  role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.admin)