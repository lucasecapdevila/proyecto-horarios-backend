# --- Importación de librerías ---
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Literal
from datetime import datetime
from contextlib import asynccontextmanager

# --- Importación de archivos locales ---
import models, schemas
from database import SessionLocal, engine, Base
from auth.auth_routes import router as auth_router
from auth.auth_utils import get_admin_user
from utils.validators import (
    validate_horario_duration,
    validate_horario_unique,
    validate_recorrido_unique,
    validate_origen_destino_different,
    validate_linea_nombre
)

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
    "https://tucubus-backend.onrender.com",
    "https://tucubus-frontend.vercel.app"
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

@app.get("/debug-db")
def debug_db():
    import os
    return {"DATABASE_URL": os.getenv("DATABASE_URL")}

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
    """Obtener todas las líneas (público, no requiere autenticación)"""
    lineas = db.query(models.Linea).all()
    return lineas

@app.get('/recorridos/', response_model=List[schemas.Recorrido], tags=["Admin"])
def get_recorridos(db: Session = Depends(get_db)):
    recorridos = db.query(models.Recorrido).options(
        joinedload(models.Recorrido.linea)
    ).all()

    resultado = []
    for r in recorridos:
        recorrido_dict = {
            "id": r.id,
            "origen": r.origen,
            "destino": r.destino,
            "linea_id": r.linea_id,
            "linea_nombre": r.linea.nombre if r.linea else None,
            "horarios": r.horarios
        }
        resultado.append(recorrido_dict)
    return resultado

@app.get('/horarios/', response_model=List[schemas.HorarioConRecorrido], tags=["Admin"], dependencies=[Depends(get_admin_user)])
def get_horarios(db: Session = Depends(get_db)):
    """Obtener todos los horarios (SOLO Administradores autenticados)"""
    horarios = db.query(models.Horario).join(models.Horario.recorrido).join(models.Recorrido.linea).all()

    resultado = []
    for h in horarios:
        resultado.append({
            "id": h.id,
            "tipo_dia": h.tipo_dia,
            "hora_salida": h.hora_salida,
            "hora_llegada": h.hora_llegada,
            "recorrido_id": h.recorrido_id,
            "directo": h.directo,
            "origen": h.recorrido.origen if h.recorrido else None,
            "destino": h.recorrido.destino if h.recorrido else None,
            "linea_nombre": h.recorrido.linea.nombre if h.recorrido.linea else None
        })
    return resultado

# ========== ENDPOINTS POST ==========
@app.post('/lineas/', response_model=schemas.Linea, status_code=status.HTTP_201_CREATED, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def crear_linea(linea: schemas.LineaCreate, db: Session = Depends(get_db)):
    """Crear línea (Solo Administradores autenticados)"""
    validate_linea_nombre(linea.nombre)
    db_linea = models.Linea(**linea.model_dump())
    db.add(db_linea)
    db.commit()
    db.refresh(db_linea)
    return db_linea

@app.put('/lineas/{linea_id}', response_model=schemas.Linea, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def update_linea(linea_id: int, linea: schemas.LineaCreate, db: Session = Depends(get_db)):
    """Actualizar línea (Solo Administradores autenticados)"""
    db_linea = db.query(models.Linea).filter(models.Linea.id == linea_id).first()
    if not db_linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    
    validate_linea_nombre(linea.nombre)
    db_linea.nombre = linea.nombre
    db.commit()
    db.refresh(db_linea)
    return db_linea

@app.delete('/lineas/{linea_id}', status_code=204, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def delete_linea(linea_id: int, db: Session = Depends(get_db)):
    """Eliminar línea (Solo Administradores autenticados)"""
    db_linea = db.query(models.Linea).filter(models.Linea.id == linea_id).first()
    if not db_linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    db.delete(db_linea)
    db.commit()
    return None

# CRUD para recorridos
@app.post('/recorridos/', response_model=schemas.Recorrido, status_code=status.HTTP_201_CREATED, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def crear_recorrido(recorrido: schemas.RecorridoCreate, db: Session = Depends(get_db)):
    """Crear recorrido (Solo Administradores autenticados)"""
    validate_origen_destino_different(recorrido.origen, recorrido.destino)

    db_linea = db.query(models.Linea).filter(models.Linea.id == recorrido.linea_id).first()
    if not db_linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    
    validate_recorrido_unique(db, recorrido.origen, recorrido.destino, recorrido.linea_id)

    db_recorrido = models.Recorrido(**recorrido.model_dump())
    db.add(db_recorrido)
    db.commit()
    db.refresh(db_recorrido)
    return db_recorrido

@app.put('/recorridos/{recorrido_id}', response_model=schemas.Recorrido, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def update_recorrido(recorrido_id: int, recorrido: schemas.RecorridoCreate, db: Session = Depends(get_db)):
    """Actualizar recorrido (Solo Administradores autenticados)"""
    db_recorrido = db.query(models.Recorrido).filter(models.Recorrido.id == recorrido_id).first()
    if not db_recorrido:
        raise HTTPException(status_code=404, detail="Recorrido no encontrado")
    
    validate_origen_destino_different(recorrido.origen, recorrido.destino)
    validate_recorrido_unique(db, recorrido.origen, recorrido.destino, recorrido.linea_id, exclude_id=recorrido_id)

    db_recorrido.origen = recorrido.origen
    db_recorrido.destino = recorrido.destino
    db_recorrido.linea_id = recorrido.linea_id
    db.commit()
    db.refresh(db_recorrido)
    return db_recorrido

@app.delete('/recorridos/{recorrido_id}', status_code=204, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def delete_recorrido(recorrido_id: int, db: Session = Depends(get_db)):
    """Eliminar recorrido (Solo Administradores autenticados)"""
    db_recorrido = db.query(models.Recorrido).filter(models.Recorrido.id == recorrido_id).first()
    if not db_recorrido:
        raise HTTPException(status_code=404, detail="Recorrido no encontrado")
    db.delete(db_recorrido)
    db.commit()
    return None

# CRUD para horarios
@app.post('/horarios/', response_model=schemas.HorarioConRecorrido, status_code=status.HTTP_201_CREATED, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def crear_horario(horario: schemas.HorarioCreate, db: Session = Depends(get_db)):
    """Crear horario (Solo Administradores autenticados)"""
    validate_horario_duration(horario.hora_salida, horario.hora_llegada)
    validate_horario_unique(db, horario.recorrido_id, horario.tipo_dia, horario.hora_salida)

    db_recorrido = db.query(models.Recorrido).join(models.Recorrido.linea).filter(models.Recorrido.id == horario.recorrido_id).first()
    if not db_recorrido:
        raise HTTPException(status_code=404, detail="Recorrido no encontrado")
    
    db_horario = models.Horario(**horario.model_dump())
    db.add(db_horario)
    db.commit()
    db.refresh(db_horario)
    return {
        "id": db_horario.id,
        "tipo_dia": db_horario.tipo_dia,
        "hora_salida": db_horario.hora_salida,
        "hora_llegada": db_horario.hora_llegada,
        "recorrido_id": db_horario.recorrido_id,
        "directo": db_horario.directo,
        "origen": db_recorrido.origen,
        "destino": db_recorrido.destino,
        "linea_nombre": db_recorrido.linea.nombre if db_recorrido.linea else None
    }

@app.put('/horarios/{horario_id}', response_model=schemas.HorarioConRecorrido, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def update_horario(horario_id: int, horario: schemas.HorarioCreate, db: Session = Depends(get_db)):
    """Actualizar horario (Solo Administradores autenticados)"""
    db_horario = db.query(models.Horario).filter(models.Horario.id == horario_id).first()
    if not db_horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    validate_horario_duration(horario.hora_salida, horario.hora_llegada)
    validate_horario_unique(db, horario.recorrido_id, horario.tipo_dia, horario.hora_salida, exclude_id=horario_id)
    
    db_recorrido = db.query(models.Recorrido).join(models.Recorrido.linea).filter(models.Recorrido.id == horario.recorrido_id).first()
    if not db_recorrido:
        raise HTTPException(status_code=404, detail="Recorrido no encontrado")

    db_horario.tipo_dia = horario.tipo_dia
    db_horario.hora_salida = horario.hora_salida
    db_horario.hora_llegada = horario.hora_llegada
    db_horario.recorrido_id = horario.recorrido_id
    db_horario.directo = horario.directo
    db.commit()
    db.refresh(db_horario)
    return {
        "id": db_horario.id,
        "tipo_dia": db_horario.tipo_dia,
        "hora_salida": db_horario.hora_salida,
        "hora_llegada": db_horario.hora_llegada,
        "recorrido_id": db_horario.recorrido_id,
        "directo": db_horario.directo,
        "origen": db_recorrido.origen,
        "destino": db_recorrido.destino,
        "linea_nombre": db_recorrido.linea.nombre if db_recorrido.linea else None
    }

@app.delete('/horarios/{horario_id}', status_code=204, tags=["Admin"], dependencies=[Depends(get_admin_user)])
def delete_horario(horario_id: int, db: Session = Depends(get_db)):
    """Eliminar horario (Solo Administradores autenticados)"""
    db_horario = db.query(models.Horario).filter(models.Horario.id == horario_id).first()
    if not db_horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    db.delete(db_horario)
    db.commit()
    return None

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

@app.get('/horarios-directos/', response_model=List[schemas.HorarioConRecorrido], tags=["App"])
def get_horarios_directos(
    origen: str,
    destino: str,
    tipo_dia: Literal["habil", "sábado", "domingo"],
    hora_actual: str = '00:00',
    db: Session = Depends(get_db)
):
    """
    Obtiene los próximos horarios directos entre dos ciudades sin conexiones.
    
    - origen: Ciudad de origen (ej: "Concepción", "San Miguel", "Leales")
    - destino: Ciudad de destino
    - tipo_dia: "habil", "sábado" o "domingo"
    - hora_actual: Filtra horarios >= esta hora (formato HH:MM, default: 00:00)
    
    Retorna los horarios ordenados por hora de salida.
    """
    # Validar hora_actual
    try:
        partes = hora_actual.split(":")
        if len(partes) != 2:
            raise ValueError()
        h, m = int(partes[0]), int(partes[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=400, 
            detail="hora_actual debe ser HH:MM entre 00:00 y 23:59"
        )
    
    horarios_completos = db.query(models.Horario).join(models.Horario.recorrido).join(models.Recorrido.linea).filter(
        models.Recorrido.origen == origen,
        models.Recorrido.destino == destino,
        models.Horario.tipo_dia == tipo_dia,
    ).order_by(models.Horario.hora_salida).all()

    if not horarios_completos:
        raise HTTPException(
            status_code=404, 
            detail=f"No existe recorrido directo o no hay horarios disponibles para {origen} → {destino} en días {tipo_dia}"
        )
    
    def str_to_minutos(hora):
        h, m = map(int, hora.split(":"))
        return h * 60 + m
    
    min_actual = str_to_minutos(hora_actual)

    horarios_filtrados = []
    for horario in horarios_completos:
        if str_to_minutos(horario.hora_salida) >= min_actual:
            horarios_filtrados.append({
                "id": horario.id,
                "tipo_dia": horario.tipo_dia,
                "hora_salida": horario.hora_salida,
                "hora_llegada": horario.hora_llegada,
                "recorrido_id": horario.recorrido_id,
                "directo": horario.directo,
                "origen": horario.recorrido.origen if horario.recorrido else None,
                "destino": horario.recorrido.destino if horario.recorrido else None,
                "linea_nombre": horario.recorrido.linea.nombre if horario.recorrido else None
            })

    if not horarios_filtrados:
        raise HTTPException(
            status_code=404,
            detail=f"No hay más horarios disponibles después de las {hora_actual}"
        )
    
    return horarios_filtrados

@app.get('/conexiones/', response_model=List[schemas.Conexion], tags=["App"])
def calcular_conexiones(
    origen: str,
    destino: str,
    tipo_dia: Literal["habil", "sábado", "domingo"],
    hora_actual: str = '00:00',
    db: Session = Depends(get_db)
):
    """
    Calcula las conexiones óptimas (Origen -> Conexión -> Destino) a partir de la hora_actual.
    """

    # Validar hora_actual 
    try:
        partes = hora_actual.split(":")
        if len(partes) != 2:
            raise ValueError()
        h, m = int(partes[0]), int(partes[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=400, detail="hora_actual debe ser HH:MM entre 00:00 y 23:59")
    
    FMT = "%H:%M"

    # 1. Encontrar posibles ciudades de conexión
    ciudades_de_salida = db.query(models.Recorrido.origen).distinct().all()
    ciudades_de_llegada = db.query(models.Recorrido.destino).distinct().all()
    ciudades_conocidas = set([c[0] for c in ciudades_de_salida] + [c[0] for c in ciudades_de_llegada])

    posibles_conexiones = [c for c in ciudades_conocidas if c != origen and c != destino]

    conexiones_encontradas = []

    for ciudad_conexion in posibles_conexiones:
        # A. Buscar RECORRIDOS para Tramo A (Origen -> Conexión)
        recorridos_a = db.query(models.Recorrido).filter(
            models.Recorrido.origen == origen,
            models.Recorrido.destino == ciudad_conexion
        ).all()

        # B. Buscar RECORRIDOS para Tramo B (Conexión -> Destino)
        recorridos_b = db.query(models.Recorrido).filter(
            models.Recorrido.origen == ciudad_conexion,
            models.Recorrido.destino == destino
        ).all()

        # C. Buscar HORARIOS para RECORRIDOS A y RECORRIDOS B, filtrando por tipo_dia
        horarios_a = db.query(models.Horario).filter(
            models.Horario.recorrido_id.in_([r.id for r in recorridos_a]),
            models.Horario.tipo_dia == tipo_dia
        ).order_by(models.Horario.hora_salida).all()

        horarios_b = db.query(models.Horario).filter(
            models.Horario.recorrido_id.in_([r.id for r in recorridos_b]),
            models.Horario.tipo_dia == tipo_dia
        ).order_by(models.Horario.hora_salida).all()
        
        # D. Buscar la conexión y filtrar por hora_actual
        def str_to_minutos(hora):
            h, m = map(int, hora.split(":"))
            return h * 60 + m
        min_actual = str_to_minutos(hora_actual)

        for horario_a in horarios_a:
            if str_to_minutos(horario_a.hora_salida) < min_actual:
                continue  # Saltar horarios antes de hora_actual

            llegada_a = datetime.strptime(horario_a.hora_llegada, FMT)

            for horario_b in horarios_b:
                try:
                    salida_b = datetime.strptime(horario_b.hora_salida, FMT)
                except ValueError:
                    continue

                # Validar la conexión: salida_b > llegada_a
                if salida_b > llegada_a:
                    diferencia = salida_b - llegada_a
                    espera_min = int(diferencia.total_seconds() / 60)

                    # Se encontró una conexión válida
                    linea_a_nombre = db.query(models.Linea.nombre).join(models.Recorrido).filter(
                        models.Recorrido.id == horario_a.recorrido_id
                    ).scalar()
                    linea_b_nombre = db.query(models.Linea.nombre).join(models.Recorrido).filter(
                        models.Recorrido.id == horario_b.recorrido_id
                    ).scalar()

                    conexion = schemas.Conexion(
                        tramo_a_salida=horario_a.hora_salida,
                        tramo_a_llegada=horario_a.hora_llegada,
                        tramo_b_salida=horario_b.hora_salida,
                        tramo_b_llegada=horario_b.hora_llegada,
                        tiempo_espera_min=espera_min,
                        ciudad_conexion=ciudad_conexion,
                        linea_a_nombre=linea_a_nombre,
                        linea_b_nombre=linea_b_nombre
                    )
                    conexiones_encontradas.append(conexion)
                    break

    if not conexiones_encontradas:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron combinaciones de conexiones posibles."
        )
    
    # Ordenar por el tiempo total de viaje
    conexiones_encontradas.sort(key=lambda c: datetime.strptime(c.tramo_a_salida, FMT))

    return conexiones_encontradas



# --- CRUD de usuarios solo para administradores ---
@app.get('/users/', response_model=List[schemas.UserOut], tags=["Usuarios"], dependencies=[Depends(get_admin_user)])
def get_usuarios(db: Session = Depends(get_db)):
    """Obtener todos los usuarios (SOLO Administradores autenticados)"""
    users = db.query(models.User).all()
    return users

@app.get('/users/{user_id}', response_model=schemas.UserOut, tags=["Usuarios"], dependencies=[Depends(get_admin_user)])
def get_usuario(user_id: int, db: Session = Depends(get_db)):
    """Obtener un usuario por id (SOLO Administradores autenticados)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@app.post('/users/', response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["Usuarios"], dependencies=[Depends(get_admin_user)])
def crear_usuario(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Crear usuario (SOLO Administradores autenticados)"""
    from auth.auth_utils import hash_password
    from auth.crud_user import get_user
    existing_user = get_user(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    hashed_password = hash_password(user.userpassword)
    db_user = models.User(username=user.username, userpassword=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put('/users/{user_id}', response_model=schemas.UserOut, tags=["Usuarios"], dependencies=[Depends(get_admin_user)])
def update_usuario(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Actualizar usuario (SOLO Administradores autenticados)"""
    from auth.auth_utils import hash_password
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db_user.username = user.username
    db_user.role = user.role
    db_user.userpassword = hash_password(user.userpassword)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete('/users/{user_id}', status_code=204, tags=["Usuarios"], dependencies=[Depends(get_admin_user)])
def delete_usuario(user_id: int, db: Session = Depends(get_db)):
    """Eliminar usuario (SOLO Administradores autenticados)"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(db_user)
    db.commit()
    return None

# --- Incluir las rutas de autenticación ---
app.include_router(auth_router)