import re

def password_strength(cls, v):
    if not re.search(r"[A-Z]", v):
      raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", v):
      raise ValueError("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r"[0-9]", v):
      raise ValueError("La contraseña debe contener al menos un número.")
    return v