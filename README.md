# API de Horarios de Colectivos

API REST para gestionar horarios de colectivos y calcular conexiones entre diferentes tramos de recorrido. Desarrollada con FastAPI y SQLAlchemy.

## 📋 Descripción

Esta API permite gestionar horarios de líneas de colectivos y calcular automáticamente las conexiones óptimas entre diferentes tramos de viaje. Está diseñada específicamente para rutas que requieren combinaciones entre dos tramos (Tramo A y Tramo B).

### Funcionalidades principales:
- **Gestión de líneas de colectivos**: CRUD completo para líneas de transporte
- **Gestión de recorridos**: Administración de rutas con origen y destino
- **Gestión de horarios**: Horarios diferenciados por tipo de día (hábil, sábado, domingo, feriado)
- **Cálculo de conexiones**: Encuentra automáticamente las mejores combinaciones entre tramos

## 🚀 Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para manejo de base de datos
- **Pydantic**: Validación de datos
- **SQLite**: Base de datos en desarrollo
- **PostgreSQL**: Base de datos en producción
- **Uvicorn**: Servidor ASGI

## 📦 Instalación

### Requisitos previos
- Python 3.8 o superior
- pip

### Pasos de instalación

1. **Clonar el repositorio**
```bash
git clone <tu-repositorio>
cd <directorio-del-proyecto>
```

2. **Crear un entorno virtual (recomendado)**
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno (opcional)**

Para usar PostgreSQL en producción, configura la variable de entorno:
```bash
export DATABASE_URL="postgresql://usuario:contraseña@host:puerto/nombre_bd"
```

Si no se configura, se usará SQLite por defecto (`horarios.db`).

## 🏃 Ejecución

### Modo desarrollo
```bash
uvicorn main:app --reload
```

### Modo producción
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación

Una vez que la API esté corriendo, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Información general**: http://localhost:8000/

## 🗂️ Estructura del Proyecto

```
.
├── main.py           # Punto de entrada de la aplicación y definición de endpoints
├── models.py         # Modelos de SQLAlchemy (tablas de BD)
├── schemas.py        # Esquemas de Pydantic (validación y serialización)
├── database.py       # Configuración de la base de datos
├── requirements.txt  # Dependencias del proyecto
└── horarios.db      # Base de datos SQLite (generada automáticamente)
```

## 🔌 Endpoints de la API

### Endpoints de Información

#### `GET /`
Devuelve información general sobre la API y sus endpoints disponibles.

**Respuesta:**
```json
{
  "nombre": "API de Horarios de Colectivos",
  "version": "1.0.0",
  "descripción": "...",
  "endpoints": {...}
}
```

---

### Endpoints de Administración (CRUD)

#### `GET /lineas/`
Lista todas las líneas de colectivos registradas.

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Línea 1",
    "recorridos": [...]
  }
]
```

#### `POST /lineas/`
Crea una nueva línea de colectivo.

**Body:**
```json
{
  "nombre": "Línea 1"
}
```

**Respuesta:** `201 Created`

---

#### `GET /recorridos/`
Lista todos los recorridos disponibles.

**Respuesta:**
```json
[
  {
    "id": 1,
    "origen": "Concepción",
    "destino": "San Miguel",
    "linea_id": 1,
    "horarios": [...]
  }
]
```

#### `POST /recorridos/`
Crea un nuevo recorrido.

**Body:**
```json
{
  "origen": "Concepción",
  "destino": "San Miguel",
  "linea_id": 1
}
```

**Respuesta:** `201 Created`

---

#### `POST /horarios/`
Crea un nuevo horario para un recorrido.

**Body:**
```json
{
  "tipo_dia": "habil",
  "hora_salida": "08:30",
  "hora_llegada": "09:15",
  "recorrido_id": 1,
  "directo": false
}
```

**Validaciones:**
- `tipo_dia`: Debe ser `"habil"`, `"sábado"`, `"domingo"` o `"feriado"`
- `hora_salida` y `hora_llegada`: Formato `HH:MM`

**Respuesta:** `201 Created`

---

### Endpoints de Aplicación

#### `GET /horarios-por-recorrido/{recorrido_id}`
Obtiene todos los horarios de un recorrido específico filtrados por tipo de día.

**Parámetros:**
- `recorrido_id` (path): ID del recorrido
- `tipo_dia` (query): Tipo de día (`habil`, `sábado`, `domingo`, `feriado`)

**Ejemplo:**
```
GET /horarios-por-recorrido/1?tipo_dia=habil
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "tipo_dia": "habil",
    "hora_salida": "08:30",
    "hora_llegada": "09:15",
    "recorrido_id": 1,
    "directo": false
  }
]
```

---

#### `GET /conexiones/`
**Endpoint principal**: Calcula las conexiones óptimas entre dos tramos de viaje.

**Parámetros:**
- `tipo_dia` (query, requerido): Tipo de día
- `direccion` (query, opcional): `"ida"` o `"vuelta"` (default: `"ida"`)

**Lógica de direcciones:**
- **Ida**: Tramo A (Concepción → San Miguel) + Tramo B (San Miguel → Leales)
- **Vuelta**: Tramo A (Leales → San Miguel) + Tramo B (San Miguel → Concepción)

**Ejemplo:**
```
GET /conexiones/?tipo_dia=habil&direccion=ida
```

**Respuesta:**
```json
[
  {
    "tramo_a_salida": "08:30",
    "tramo_a_llegada": "09:15",
    "tramo_b_salida": "09:30",
    "tramo_b_llegada": "10:45",
    "tiempo_espera_min": 15
  }
]
```

**Algoritmo de conexiones:**
1. Obtiene todos los horarios del Tramo A para el tipo de día especificado
2. Obtiene todos los horarios del Tramo B para el tipo de día especificado
3. Para cada horario del Tramo A, busca el primer horario del Tramo B que salga **después** de la llegada del Tramo A
4. Calcula el tiempo de espera en minutos
5. Devuelve todas las conexiones válidas encontradas

---

## 🗄️ Modelo de Datos

### Linea
- `id`: Integer (PK)
- `nombre`: String (Unique)

### Recorrido
- `id`: Integer (PK)
- `origen`: String
- `destino`: String
- `linea_id`: Integer (FK → Linea)

### Horario
- `id`: Integer (PK)
- `tipo_dia`: String (habil, sábado, domingo, feriado)
- `hora_salida`: String (formato HH:MM)
- `hora_llegada`: String (formato HH:MM)
- `directo`: Boolean (default: False)
- `recorrido_id`: Integer (FK → Recorrido)

---

## 🔧 Configuración Avanzada

### CORS
Por defecto, la API acepta peticiones desde `http://localhost:5173`. Para modificar los orígenes permitidos, edita el array `origins` en `main.py`:

```python
origins = [
    "http://localhost:5173",
    "http://localhost:3000",  # Agregar más orígenes
]
```

### Base de Datos

#### Desarrollo (SQLite)
La base de datos se crea automáticamente en `./horarios.db` al iniciar la aplicación.

#### Producción (PostgreSQL)
Configura la variable de entorno `DATABASE_URL`:
```bash
export DATABASE_URL="postgresql://usuario:contraseña@host:puerto/bd"
```

El sistema detecta automáticamente si estás usando PostgreSQL y ajusta la configuración.

---

## 📝 Ejemplos de Uso

### Crear una línea y un recorrido completo

```python
import requests

base_url = "http://localhost:8000"

# 1. Crear línea
linea = requests.post(f"{base_url}/lineas/", json={"nombre": "Línea 1"})
linea_id = linea.json()["id"]

# 2. Crear recorrido
recorrido = requests.post(f"{base_url}/recorridos/", json={
    "origen": "Concepción",
    "destino": "San Miguel",
    "linea_id": linea_id
})
recorrido_id = recorrido.json()["id"]

# 3. Crear horarios
horarios = [
    {"hora_salida": "08:30", "hora_llegada": "09:15"},
    {"hora_salida": "10:00", "hora_llegada": "10:45"},
]

for h in horarios:
    requests.post(f"{base_url}/horarios/", json={
        "tipo_dia": "habil",
        "hora_salida": h["hora_salida"],
        "hora_llegada": h["hora_llegada"],
        "recorrido_id": recorrido_id,
        "directo": False
    })
```

### Buscar conexiones

```python
# Buscar conexiones para día hábil en dirección ida
response = requests.get(
    f"{base_url}/conexiones/",
    params={"tipo_dia": "habil", "direccion": "ida"}
)

conexiones = response.json()
for c in conexiones:
    print(f"Salida Tramo A: {c['tramo_a_salida']}")
    print(f"Llegada Tramo A: {c['tramo_a_llegada']}")
    print(f"Salida Tramo B: {c['tramo_b_salida']}")
    print(f"Espera: {c['tiempo_espera_min']} minutos")
    print("---")
```

---

## ⚠️ Notas Importantes

1. **IDs hardcodeados**: El endpoint `/conexiones/` utiliza IDs fijos para los tramos (1, 2, 3, 4). Asegúrate de crear los recorridos en este orden:
   - ID 1: Concepción → San Miguel (ida)
   - ID 2: San Miguel → Leales (ida)
   - ID 3: Leales → San Miguel (vuelta)
   - ID 4: San Miguel → Concepción (vuelta)

2. **Formato de horarios**: Siempre usa el formato `HH:MM` (24 horas)

3. **Tipos de día**: Los valores válidos son exactamente: `"habil"`, `"sábado"`, `"domingo"`, `"feriado"`

---

## 🐛 Solución de Problemas

### Error: "No se encontraron horarios"
- Verifica que existan horarios para el `tipo_dia` especificado
- Confirma que los IDs de recorrido sean correctos

### Error: "Línea/Recorrido no encontrado"
- Asegúrate de que el ID referenciado exista en la base de datos
- Usa `GET /lineas/` o `GET /recorridos/` para verificar los IDs disponibles

### Error de formato en horarios
- Verifica que las horas estén en formato `HH:MM` (ejemplo: `08:30`, no `8:30`)

---

## 📄 Licencia

[Especifica tu licencia aquí]

## 👥 Contribución

Las contribuciones son bienvenidas. Para cambios importantes, por favor abre un issue primero para discutir los cambios propuestos.

## 📧 Contacto

[LinkedIn](https://www.linkedin.com/in/lucasecapdevila/)