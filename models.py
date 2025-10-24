from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base

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
  directo = Column(Boolean, default=False)
  linea_id = Column(Integer, ForeignKey("lineas.id"))
  linea = relationship("Linea", back_populates="recorridos")
  horarios = relationship("Horario", back_populates="recorrido")

class Horario(Base):
  __tablename__ = "horarios"

  id = Column(Integer, primary_key=True)
  tipo_dia = Column(String)
  hora_salida = Column(String)
  hora_llegada = Column(String)
  recorrido_id = Column(Integer, ForeignKey("recorridos.id"))
  recorrido = relationship("Recorrido", back_populates="horarios")