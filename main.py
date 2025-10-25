# --- Importación de librerías ---
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from datetime import datetime
from contextlib import asynccontextmanager

# --- Importación de archivos locales ---
import models, schemas
from database import SessionLocal, engine, Base

# --- Importación del middleware de CORS ---
from fastapi.middleware.cors import CORSMiddleware

# --- Lifespan crea las tablas al iniciar la app ---
@asynccontextmanager
async def lifespan(app: FastAPI):
  Base.metadata.create_all(bind=engine)
  yield

# --- Inicialización de la aplicación FastAPI ---
app = FastAPI(
  title="API de Horarios de Colectivos",
  description="API para gestionar horarios de colectivos utilizando FastAPI y SQLAlchemy.",
  version="1.0.0",
  lifespan=lifespan
)

# --- Configuración del middleware de CORS ---
origins = [
  "http://localhost:5173",
  "http://localhost:3000",
  "https://api-horarios-8uro.onrender.com/"
]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# --- Dependencia para obtener la sesión de la base de datos ---
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

# --- Rutas de la API ---
# ========== ENDPOINT RAÍZ ==========
@app.get('/', tags=["Info"])
async def raiz():
  return {
    "nombre": "API de Horarios de Colectivos",
    "version": "1.0.0",
    "descripción": "API REST para gestionar horarios de colectivos y conexiones utilizando FastAPI y SQLAlchemy.",
    "documentación": "Visita /docs para la documentación interactiva con Swagger de la API.",
    "endpoints": {
      "GET /": "Información sobre la API.",
      "GET /docs": "Documentación interactiva con Swagger.",
      "App": {
        "GET /horarios-por-recorrido/{id}?tipo_dia=...": "Lista de horarios para un recorrido específico y tipo de día.",
        "GET /conexiones?tipo_dia=...": "Calcula las conexiones entre recorridos basándose en los horarios."
      },
      "Admin (CRUD)": {
        "GET /lineas": "Lista todas las líneas de colectivos.",
        "POST /lineas": "Crea una nueva línea de colectivo.",
        "GET /recorridos": "Lista todos los recorridos.",
        "POST /recorridos": "Crea un nuevo recorrido.",
        "POST /horarios": "Crea un nuevo horario.",
      }
    }
  }

# ========== ENDPOINTS GET ==========
@app.get('/lineas/', response_model=List[schemas.Linea], tags=["Admin"])
def get_lineas(db: Session = Depends(get_db)):
  lineas = db.query(models.Linea).all()
  return lineas

@app.get('/recorridos/', response_model=List[schemas.Recorrido], tags=["Admin"])
def get_recorridos(db: Session = Depends(get_db)):
  recorridos = db.query(models.Recorrido).all()
  return recorridos

# ========== ENDPOINTS POST ==========
@app.post('/lineas/', response_model=schemas.Linea, status_code=status.HTTP_201_CREATED, tags=["Admin"])
def crear_linea(linea: schemas.LineaCreate, db: Session = Depends(get_db)):
  db_linea = models.Linea(nombre=linea.nombre)
  db.add(db_linea)
  db.commit()
  db.refresh(db_linea)
  return db_linea

@app.post('/recorridos/', response_model=schemas.Recorrido, status_code=status.HTTP_201_CREATED, tags=["Admin"])
def crear_recorrido(recorrido: schemas.RecorridoCreate, db: Session = Depends(get_db)):
  # Verificar que la línea existe
  db_linea = db.query(models.Linea).filter(models.Linea.id == recorrido.linea_id).first()
  if not db_linea:
    raise HTTPException(status_code=404, detail="Línea no encontrada")
  
  db_recorrido = models.Recorrido(**recorrido.model_dump())
  db.add(db_recorrido)
  db.commit()
  db.refresh(db_recorrido)
  return db_recorrido

@app.post('/horarios/', response_model=schemas.Horario, status_code=status.HTTP_201_CREATED, tags=["Admin"])
def crear_horario(horario: schemas.HorarioCreate, db: Session = Depends(get_db)):
  # Verificar que el recorrido existe
  db_recorrido = db.query(models.Recorrido).filter(models.Recorrido.id == horario.recorrido_id).first()
  if not db_recorrido:
    raise HTTPException(status_code=404, detail="Recorrido no encontrado")
  
  db_horario = models.Horario(**horario.model_dump())
  db.add(db_horario)
  db.commit()
  db.refresh(db_horario)
  return db_horario

# ========== ENDPOINTS COMPLEJOS ==========
@app.get('/horarios-por-recorrido/{recorrido_id}', response_model=List[schemas.Horario], tags=["App"])
def get_horarios_por_recorrido(
  recorrido_id: int,
  tipo_dia: Literal["habil", "feriado", "sábado", "domingo"],
  db: Session = Depends(get_db)
  ):
  # Devuelve los horarios para un recorrido específico, filtrado por tipo de día
  horarios = db.query(models.Horario).filter(
    models.Horario.recorrido_id == recorrido_id,
    models.Horario.tipo_dia == tipo_dia
  ).order_by(models.Horario.hora_salida).all()

  if not horarios:
    raise HTTPException(status_code=404, detail="No se encontraron horarios")
  
  return horarios

@app.get('/conexiones/', response_model=List[schemas.Conexion], tags=["App"])
def get_conexiones(
  tipo_dia: Literal["habil", "feriado", "sábado", "domingo"],
  direccion: Literal["ida", "vuelta"] = "ida",
  db: Session = Depends(get_db)
):
  # Este es el principal endpoint. Busca conexiones entre el Tramo A y el Tramo B
  # Dependiendo de la dirección, se asignan los tramos correspondientes
  # dirección "ida": Tramo A = Concepción -> San Miguel, Tramo B = San Miguel -> Leales
  # dirección "vuelta": Tramo A = Leales -> San Miguel, Tramo B = San Miguel -> Concepción

  # Asignamos los IDs de los tramos según la dirección
  if direccion == "ida":
    ID_TRAMO_A = 1  # ID del Recorrido Tramo A
    id_TRAMO_B = 2  # ID del Recorrido Tramo B
  else:  # dirección == "vuelta"
    ID_TRAMO_A = 3  # ID del Recorrido Tramo A (vuelta)
    id_TRAMO_B = 4  # ID del Recorrido Tramo B (vuelta)

  # Obtener horarios del Tramo A
  horarios_tramo_a = db.query(models.Horario).filter(
    models.Horario.recorrido_id == ID_TRAMO_A,
    models.Horario.tipo_dia == tipo_dia
  ).order_by(models.Horario.hora_salida).all()

  # Obtener horarios del Tramo B
  horarios_tramo_b = db.query(models.Horario).filter(
    models.Horario.recorrido_id == id_TRAMO_B,
    models.Horario.tipo_dia == tipo_dia
  ).order_by(models.Horario.hora_salida).all()

  if not horarios_tramo_a or not horarios_tramo_b:
    raise HTTPException(status_code=404, detail="No se encontraron horarios para la conexión en ese tipo de día")
  
  # Buscar conexiones
  conexiones_encontradas = []
  FMT = "%H:%M"
  for horario_a in horarios_tramo_a:
    for horario_b in horarios_tramo_b:
      try:
        llegada_a = datetime.strptime(horario_a.hora_llegada, FMT)
        salida_b = datetime.strptime(horario_b.hora_salida, FMT)
      except ValueError:
        continue  # Saltar horarios con formato incorrecto

      # Si la salida del Tramo B es DESPUÉS de la llegada del Tramo A
      if salida_b > llegada_a:
        #* Se encuentra una conexión válida
        diferencia = salida_b - llegada_a
        espera_min = int(diferencia.total_seconds() / 60)

        conexion = schemas.Conexion(
          tramo_a_salida=horario_a.hora_salida,
          tramo_a_llegada=horario_a.hora_llegada,
          tramo_b_salida=horario_b.hora_salida,
          tramo_b_llegada=horario_b.hora_llegada,
          tiempo_espera_min=espera_min
        )
        conexiones_encontradas.append(conexion)
        break  # Pasar al siguiente horario del Tramo A después de encontrar la primera conexión válida

  if not conexiones_encontradas:
    raise HTTPException(status_code=404, detail="No se encontraron combinaciones")
  
  return conexiones_encontradas