import re
from fastapi import HTTPException

def password_strength(password: str) -> str:
    """Valida que la contraseña cumpla con los requisitos mínimos de seguridad."""
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r"[0-9]", password):
        raise ValueError("La contraseña debe contener al menos un número.")
    return password

def validar_hora(hora: str):
    if not re.match(r"^\d{2}:\d{2}$", hora):
        raise ValueError("El formato de hora debe ser HH:MM")
    return True

# ==================== NUEVAS VALIDACIONES ====================

def time_to_minutes(time_str: str) -> int:
    """Convierte hora HH:MM a minutos desde medianoche"""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def calculate_trip_duration(hora_salida: str, hora_llegada: str) -> int:
    """
    Calcula la duración del viaje en minutos.
    Considera el paso de medianoche.
    """
    salida_min = time_to_minutes(hora_salida)
    llegada_min = time_to_minutes(hora_llegada)
    
    # Si llegada < salida, el viaje cruza medianoche
    if llegada_min < salida_min:
        llegada_min += 24 * 60
    
    return llegada_min - salida_min

def validate_horario_duration(hora_salida: str, hora_llegada: str) -> None:
    """
    Valida que la duración del viaje sea razonable.
    Lanza HTTPException si es inválida.
    """
    duracion = calculate_trip_duration(hora_salida, hora_llegada)
    
    # Duración mínima: 5 minutos
    if duracion < 5:
        raise HTTPException(
            status_code=400,
            detail="El viaje debe durar al menos 5 minutos"
        )
    
    # Duración máxima: 10 horas (600 minutos)
    if duracion > 600:
        raise HTTPException(
            status_code=400,
            detail="El viaje no puede durar más de 10 horas"
        )

def validate_recorrido_unique(db, origen: str, destino: str, linea_id: int, exclude_id: int = None):
    """
    Valida que no exista un recorrido duplicado EN LA MISMA LÍNEA.
    Dos líneas diferentes SÍ pueden tener el mismo origen-destino.
    exclude_id se usa al actualizar para excluir el registro actual.
    """
    from models import Recorrido
    
    query = db.query(Recorrido).filter(
        Recorrido.origen == origen,
        Recorrido.destino == destino,
        Recorrido.linea_id == linea_id  # CLAVE: Solo validar en la misma línea
    )
    
    if exclude_id:
        query = query.filter(Recorrido.id != exclude_id)
    
    existing = query.first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un recorrido {origen} → {destino} en esta línea"
        )

def validate_origen_destino_different(origen: str, destino: str) -> None:
    """Valida que origen y destino sean diferentes"""
    if origen.strip().lower() == destino.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="El origen y destino no pueden ser iguales"
        )

def validate_horario_unique(db, recorrido_id: int, tipo_dia: str, hora_salida: str, exclude_id: int = None):
    """
    Valida que no exista un horario duplicado EN EL MISMO RECORRIDO.
    - Mismo recorrido + mismo tipo_dia + misma hora_salida = DUPLICADO
    - Diferentes recorridos pueden tener la misma hora (aunque sean de la misma línea)
    """
    from models import Horario
    
    query = db.query(Horario).filter(
        Horario.recorrido_id == recorrido_id,  # CLAVE: Solo validar en el mismo recorrido
        Horario.tipo_dia == tipo_dia,
        Horario.hora_salida == hora_salida
    )
    
    if exclude_id:
        query = query.filter(Horario.id != exclude_id)
    
    existing = query.first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un horario para este recorrido a las {hora_salida} en días {tipo_dia}"
        )

def validate_linea_nombre(nombre: str) -> None:
    """Valida el nombre de una línea"""
    if not nombre or len(nombre.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="El nombre de la línea debe tener al menos 2 caracteres"
        )
    
    if len(nombre) > 50:
        raise HTTPException(
            status_code=400,
            detail="El nombre de la línea no puede exceder 50 caracteres"
        )