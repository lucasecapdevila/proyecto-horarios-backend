from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# --- Esquemas para Horarios ---
class HorarioBase(BaseModel):
  tipo_dia: Literal["habil", "feriado", "sábado", "domingo"]
  hora_salida: str = Field(..., pattern=r"^\d{2}:\d{2}$")
  hora_llegada: str = Field(..., pattern=r"^\d{2}:\d{2}$")

class HorarioCreate(HorarioBase):
  pass

class Horario(HorarioBase):
  id: int
  class Config:
    orm_mode = True

# --- Esquemas para Recorridos ---
class RecorridoBase(BaseModel):
  origen: str
  destino: str
  directo: bool = False
  linea_id: int

class RecorridoCreate(RecorridoBase):
  pass

class Recorrido(RecorridoBase):
  id: int
  horarios: List[Horario] = []
  class Config:
    orm_mode = True

# --- Esquemas para Lineas ---
class LineaBase(BaseModel):
  nombre: str

class LineaCreate(LineaBase):
  pass

class Linea(LineaBase):
  id: int
  recorridos: List[Recorrido] = []
  class Config:
    orm_mode = True

# --- Esquema para la Conexión ---
class Conexion(BaseModel):
  tramo_1_salida: str
  tramo_1_llegada: str
  tramo_2_salida: str
  tramo_2_llegada: str
  tiempo_espera_min: int