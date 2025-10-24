# --- Importación de librerías ---
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

# --- Importación de archivos locales ---
from . import models, schemas
from .database import SessionLocal, engine, Base

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

