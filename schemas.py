from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from models import RoleEnum
from utils.validators import password_strength

# --- Esquemas para Horarios ---
class HorarioBase(BaseModel):
  tipo_dia: Literal["habil", "feriado", "sábado", "domingo"]
  hora_salida: str = Field(..., pattern=r"^\d{2}:\d{2}$")
  hora_llegada: str = Field(..., pattern=r"^\d{2}:\d{2}$")
  recorrido_id: int
  directo: bool = False

class HorarioCreate(HorarioBase):
  pass

class Horario(HorarioBase):
  id: int
  class Config:
    from_attributes = True

# --- Esquemas para Recorridos ---
class RecorridoBase(BaseModel):
  origen: str
  destino: str
  linea_id: int

class RecorridoCreate(RecorridoBase):
  pass

class Recorrido(RecorridoBase):
  id: int
  horarios: List[Horario] = []
  class Config:
    from_attributes = True

# --- Esquemas para Lineas ---
class LineaBase(BaseModel):
  nombre: str

class LineaCreate(LineaBase):
  pass

class Linea(LineaBase):
  id: int
  recorridos: List[Recorrido] = []
  class Config:
    from_attributes = True

# --- Esquema para la Conexión ---
class Conexion(BaseModel):
  tramo_a_salida: str
  tramo_a_llegada: str
  tramo_b_salida: str
  tramo_b_llegada: str
  tiempo_espera_min: int

class UserBase(BaseModel):
  username: str = Field(..., min_length=3, max_length=25)
  role: Optional[RoleEnum] = RoleEnum.admin

class UserCreate(UserBase):
  userpassword: str = Field(..., min_length=12)

  @field_validator('userpassword')
  def validate_password(cls, v):
    # Validar requisitos de seguridad de la contraseña
    return password_strength(v)
  
class UserOut(UserBase):
  id: int
  class Config:
    from_attributes = True

class UserLogin(BaseModel):
    username: str
    userpassword: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"