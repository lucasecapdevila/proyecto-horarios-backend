import re

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