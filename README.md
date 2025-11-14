# TucuBus API - Backend

API REST para la gestión de horarios de colectivos y conexiones entre diferentes ciudades de Tucumán.

## Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para manejo de base de datos
- **PostgreSQL/SQLite**: Base de datos (PostgreSQL en producción, SQLite en desarrollo)
- **JWT + bcrypt**: Autenticación y seguridad
- **Pydantic**: Validación de datos

## Estructura del Proyecto

```
├── main.py                 # Aplicación principal y endpoints
├── models.py              # Modelos de base de datos (SQLAlchemy)
├── schemas.py             # Esquemas de validación (Pydantic)
├── database.py            # Configuración de base de datos
├── auth/
│   ├── auth_routes.py     # Endpoints de autenticación
│   ├── auth_utils.py      # Utilidades JWT y password hashing
│   └── crud_user.py       # Operaciones de usuario
└── utils/
    └── validators.py      # Validaciones de negocio
```

## Modelos de Datos

### Linea
Representa una línea de colectivo (ej: "Línea 101", "Chevallier").

### Recorrido
Define un trayecto específico con origen y destino dentro de una línea.

### Horario
Especifica horarios de salida/llegada para cada recorrido según tipo de día (hábil, sábado, domingo).

### User
Usuarios del sistema con roles (admin/user) para gestión de la API.

## Autenticación

Sistema basado en JWT con dos roles:
- **Admin**: Acceso completo CRUD
- **User**: Acceso limitado (futuras funcionalidades)

### Endpoints de Autenticación
- `POST /auth/register` - Registro de nuevos usuarios
- `POST /auth/login` - Login (retorna JWT token)
- `GET /auth/me` - Información del usuario autenticado

## Endpoints Principales

### Públicos (App)
- `GET /horarios-directos/` - Horarios directos entre dos ciudades
- `GET /conexiones/` - Calcula conexiones óptimas con transbordos
- `GET /horarios-por-recorrido/{id}` - Horarios de un recorrido específico

### Administración (requiere JWT admin)
- **Líneas**: `GET, POST, PUT, DELETE /lineas/`
- **Recorridos**: `GET, POST, PUT, DELETE /recorridos/`
- **Horarios**: `GET, POST, PUT, DELETE /horarios/`
- **Usuarios**: `GET, POST, PUT, DELETE /users/`

## Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (.env)
SECRET_JWT=tu_clave_secreta
ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
DATABASE_URL=sqlite:///./horarios.db  # o PostgreSQL en producción

# Ejecutar servidor
uvicorn main:app --reload
```

## CORS

Configurado para permitir requests desde:
- `http://localhost:5173` (Vite dev)
- `http://localhost:3000` (React dev)
- Dominios de producción en Render/Vercel

## Validaciones

El sistema incluye validaciones robustas:
- Contraseñas seguras (mayúscula, minúscula, número, 12+ caracteres)
- Horarios válidos (HH:MM, duración 5min-10h)
- No duplicados (recorridos/horarios únicos por línea)
- Origen ≠ Destino

## Algoritmo de Conexiones

El endpoint `/conexiones/` encuentra rutas óptimas considerando:
1. Ciudades intermedias disponibles
2. Sincronización de horarios (llegada < siguiente salida)
3. Tiempo de espera entre transbordos
4. Filtrado por hora actual

## Seguridad

- Passwords hasheados con bcrypt
- Tokens JWT con expiración
- Middleware de autenticación por ruta
- Validación de roles para operaciones administrativas

## Documentación Interactiva

Una vez iniciado el servidor, accede a:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Estado del Proyecto

**Versión**: 1.0.0  
**Estado**: En producción  
**Deploy**: Render (backend) + [Vercel](https://tucubus-frontend.vercel.app/) (frontend)