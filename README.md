# 🤖 APIChatBot - FastAPI ChatBot API

Una API moderna de chatbot construida con FastAPI que permite crear, gestionar y procesar preguntas con contexto de texto o archivos PDF, organizadas por categorías y con sistema de autenticación.

## 🚀 Características

- **🔐 Autenticación JWT**: Sistema completo de registro, login y gestión de usuarios
- **💬 Gestión de Preguntas**: Crear preguntas con contexto de texto o archivos PDF
- **📁 Sistema de Categorías**: Organización jerárquica de preguntas por categorías
- **📄 Procesamiento de PDFs**: Subida y procesamiento de archivos PDF como contexto
- **🔍 Búsqueda y Filtros**: Sistema avanzado de búsqueda y filtrado de preguntas
- **🧠 Embeddings Vectoriales**: Búsqueda semántica con pgvector y PostgreSQL
- **📊 Paginación**: Respuestas paginadas para mejor rendimiento
- **📧 Recuperación de Contraseña**: Sistema de reset de contraseña por email
- **👤 Gestión de Perfiles**: Actualización de perfiles de usuario
- **🗂️ Almacenamiento en la Nube**: Integración con MinIO para almacenamiento de archivos
- **🐳 Docker Ready**: Configuración completa para contenedores

## 🛠️ Tecnologías

- **Backend**: FastAPI 0.104+
- **Base de Datos**: PostgreSQL 16 + pgvector para embeddings vectoriales
- **ORM**: SQLAlchemy 2.0 con soporte asíncrono
- **Autenticación**: JWT con python-jose
- **Almacenamiento**: MinIO (S3-compatible)
- **Email**: aiosmtplib para notificaciones
- **Migraciones**: Alembic
- **Testing**: pytest + pytest-asyncio
- **Contenedores**: Docker + Docker Compose

## 📋 Requisitos

- Python 3.11+ (probado con Python 3.12)
- Docker y Docker Compose (requerido para PostgreSQL y MinIO)
- Poetry (recomendado) o pip con venv
- Servidor SMTP (opcional, para emails)

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd APIChatBot
```

### 2. Configurar el entorno

#### Opción A: Con Poetry (Recomendado)

```bash
# Instalar Poetry si no lo tienes
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias
poetry install

# Activar el entorno virtual
poetry shell
```

#### Opción B: Con pip y venv (Alternativa)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias adicionales requeridas
pip install pydantic-settings

# Las dependencias ya están instaladas en el venv incluido
```

### 3. Configurar variables de entorno

Crea un archivo `.env` basado en la plantilla:

```bash
cp env.template .env
```

Las variables principales ya están configuradas en el archivo `.env`. Las más importantes son:

```env
# Base de datos PostgreSQL (CONFIGURADO)

# JWT (CONFIGURADO)
SECRET_KEY=a8f5f167f44f4964e6c998dee827110c
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MinIO/S3 (CONFIGURADO)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=chatbot-files
MINIO_SECURE=false

# Email SMTP (OPCIONAL - configurar si necesitas)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-de-aplicación
SMTP_FROM_EMAIL=tu-email@gmail.com

# OpenAI para embeddings (OPCIONAL)
OPENAI_API_KEY=tu-openai-api-key

# Configuración del servidor (CONFIGURADO)
HOST=0.0.0.0
PORT=8000
```

### 4. Levantar servicios con Docker Compose

```bash
# Levantar PostgreSQL y MinIO (REQUERIDO)
docker-compose up -d db minio

# Verificar que los servicios están funcionando
docker-compose ps
```

### 5. Inicializar la base de datos

```bash
# Activar entorno virtual
source venv/bin/activate  # o poetry shell

# Ejecutar migraciones (crea todas las tablas automáticamente)
alembic upgrade head

# Crear usuario administrador por defecto
python src/app/db/init_db.py
```

**✅ Estado después de la inicialización:**
- Base de datos PostgreSQL 16 con pgvector v0.8.1
- 5 tablas creadas: users, categories, questions, chunk_embeddings, alembic_version
- Extensión pgvector configurada para embeddings vectoriales
- **Usuario administrador por defecto creado** (admin@chatbot.local / admin123)

### 6. Configurar usuario administrador (Opcional)

El sistema crea automáticamente un usuario administrador con las siguientes credenciales por defecto:

- **Email**: admin@chatbot.local
- **Contraseña**: admin123
- **Rol**: admin

Para personalizar estas credenciales, agrega las siguientes variables a tu archivo `.env`:

```env
# Usuario administrador por defecto
DEFAULT_ADMIN_EMAIL=tu-admin@ejemplo.com
DEFAULT_ADMIN_PASSWORD=tu-contraseña-segura
DEFAULT_ADMIN_NAME=Tu Nombre
DEFAULT_ADMIN_ROLE=admin
```

**Comandos útiles para gestión de usuarios:**

```bash
# Crear usuario por defecto manualmente
python scripts/init_default_user.py

# Con Docker (si usas contenedores)
make init-user

# Verificar que el usuario fue creado
# Puedes usar la API en http://localhost:8000/docs para hacer login
```

## 🏃‍♂️ Ejecutar la aplicación

### Desarrollo (Método Recomendado)

```bash
# 1. Asegúrate de que los servicios estén corriendo
docker-compose up -d db minio

# 2. Activar entorno virtual
source venv/bin/activate  # o poetry shell

# 3. Ejecutar la API en modo desarrollo
python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

**✅ Servicios disponibles:**
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### Producción

```bash
# Con Gunicorn (recomendado para producción)
gunicorn src.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Con Docker
docker build -t apichatbot .
docker run -p 8000:8000 apichatbot
```

La API estará disponible en: `http://localhost:8000`

## 🎯 **Configuración Completada - Estado Actual**

### ✅ **Servicios Funcionando:**

| Servicio | URL | Estado | Credenciales |
|----------|-----|--------|--------------|
| **FastAPI** | http://localhost:8000 | ✅ Activo | - |
| **PostgreSQL** | localhost:5432 | ✅ Activo | chatbot_user/chatbot_password |
| **MinIO Console** | http://localhost:9001 | ✅ Activo | minioadmin/minioadmin |
| **MinIO API** | http://localhost:9000 | ✅ Activo | - |

### 📊 **Base de Datos PostgreSQL:**
- **Versión**: PostgreSQL 16
- **Extensión**: pgvector v0.8.1 (instalada y funcionando)
- **Base de datos**: `chatbot_db`
- **Usuario**: `chatbot_user`
- **Tablas creadas**: 5 (users, categories, questions, chunk_embeddings, alembic_version)

### 🔧 **Comandos de Desarrollo Diario:**

```bash
# Iniciar servicios
docker-compose up -d db minio

# Activar entorno
source venv/bin/activate

# Inicializar base de datos (primera vez)
alembic upgrade head
python src/app/db/init_db.py  # Crea tablas y usuario por defecto

# Ejecutar API
python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Verificar salud
curl http://localhost:8000/health
```

### 🛠️ **Comandos de Base de Datos:**

```bash
# Conectar a PostgreSQL
docker-compose exec db psql -U chatbot_user -d chatbot_db

# Ver tablas
docker-compose exec db psql -U chatbot_user -d chatbot_db -c "\dt"

# Verificar pgvector
docker-compose exec db psql -U chatbot_user -d chatbot_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

# Nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head
```

## 📚 Documentación de la API

Una vez que la aplicación esté ejecutándose, puedes acceder a:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🔗 Endpoints Principales

### Autenticación
- `POST /register` - Registrar nuevo usuario
- `POST /login` - Iniciar sesión
- `POST /request-password-reset` - Solicitar reset de contraseña

### Preguntas
- `POST /chat/questions` - Crear nueva pregunta
- `GET /chat/questions` - Listar preguntas (con paginación y filtros)
- `POST /chat/questions/{question_id}/approve` - Aprobar/desactivar pregunta
- `GET /chat/questions/{question_id}/download` - Descargar archivo PDF

### Categorías
- `POST /chat/categories` - Crear categoría
- `GET /chat/categories` - Listar categorías
- `GET /chat/categories/tree` - Obtener árbol de categorías
- `PUT /chat/categories/{category_id}` - Actualizar categoría
- `DELETE /chat/categories/{category_id}` - Eliminar categoría

### Perfil
- `GET /profile` - Obtener perfil del usuario
- `PUT /profile` - Actualizar perfil

### Embeddings Vectoriales
- `POST /embeddings/create` - Crear embeddings para una pregunta
- `POST /embeddings/search` - Búsqueda semántica por similitud
- `GET /embeddings/question/{question_id}` - Obtener embeddings de una pregunta
- `DELETE /embeddings/question/{question_id}` - Eliminar embeddings
- `GET /embeddings/stats` - Estadísticas de embeddings

### Salud
- `GET /` - Mensaje de bienvenida
- `GET /health` - Check de salud de la API

## 🗂️ Estructura del Proyecto

```
APIChatBot/
├── src/app/
│   ├── controllers/          # Controladores/Rutas de la API
│   │   ├── auth.py          # Autenticación
│   │   ├── question.py      # Gestión de preguntas
│   │   ├── category.py      # Gestión de categorías
│   │   └── profile.py       # Gestión de perfiles
│   ├── models/              # Modelos de base de datos
│   │   ├── user.py         # Modelo de usuario
│   │   ├── question.py     # Modelo de pregunta
│   │   └── category.py     # Modelo de categoría
│   ├── schemas/             # Esquemas Pydantic
│   │   ├── user.py         # Esquemas de usuario
│   │   ├── question.py     # Esquemas de pregunta
│   │   └── category.py     # Esquemas de categoría
│   ├── services/            # Lógica de negocio
│   │   ├── user_service.py # Servicio de usuarios
│   │   ├── email_service.py# Servicio de email
│   │   └── storage_service.py # Servicio de almacenamiento
│   ├── db/                  # Configuración de base de datos
│   │   ├── database.py     # Configuración SQLAlchemy
│   │   └── session.py      # Sesiones de DB
│   ├── utils/               # Utilidades
│   │   ├── jwt_utils.py    # Utilidades JWT
│   │   └── hashing.py      # Hash de contraseñas
│   ├── dependencies/        # Dependencias FastAPI
│   │   └── auth.py         # Dependencias de autenticación
│   ├── middlewares/         # Middlewares
│   │   ├── auth_middleware.py
│   │   └── logging_middleware.py
│   └── main.py             # Aplicación principal
├── migrations/              # Migraciones Alembic
├── tests/                   # Tests
├── scripts/                 # Scripts de utilidad
├── uploads/                 # Directorio de archivos (desarrollo)
├── docker-compose.minio.yml # Docker Compose para MinIO
├── Dockerfile              # Imagen Docker
├── pyproject.toml          # Configuración Poetry
└── alembic.ini            # Configuración Alembic
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con cobertura
pytest --cov=src

# Ejecutar tests específicos
pytest tests/test_main.py -v
```

## 🐳 Docker

### Configuración inicial con Docker

```bash
# 1. Configurar variables de entorno
cp docker.env.template .env
# Edita el archivo .env con tus configuraciones

# 2. Usar Makefile (recomendado)
make setup    # Configuración inicial completa
make up       # Levantar servicios
make logs     # Ver logs

# 3. O usar Docker Compose directamente
docker-compose build
docker-compose up -d
```

### Comandos útiles con Makefile

```bash
# Gestión de servicios
make up           # Levantar todos los servicios
make down         # Parar todos los servicios
make restart      # Reiniciar servicios
make rebuild      # Reconstruir y levantar

# Desarrollo
make dev          # Modo desarrollo con logs
make logs-api     # Ver logs solo de la API
make shell        # Acceder al contenedor
make migrate      # Ejecutar migraciones

# Mantenimiento
make clean        # Limpiar recursos Docker
make backup       # Crear backup de datos
make health       # Verificar salud de servicios
```

### Servicios incluidos

- **API FastAPI**: `http://localhost:8000`
- **MinIO Console**: `http://localhost:9001` (admin/minioadmin)
- **MinIO API**: `http://localhost:9000`

### Desarrollo con Docker Compose

```bash
# Levantar toda la infraestructura
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f api

# Reconstruir solo la API
docker-compose build api
docker-compose up -d api

# Ejecutar migraciones
docker-compose exec api alembic upgrade head

# Inicializar base de datos con usuario por defecto
make init-db

# Crear solo el usuario por defecto
make init-user

# Comandos locales (sin Docker)
make init-db-local
make init-user-local

# Acceder al contenedor
docker-compose exec api bash

# Parar servicios
docker-compose down
```

## 🔧 Configuración Avanzada

### Base de Datos

#### PostgreSQL con pgvector (Recomendado para Producción)

El proyecto está configurado para usar PostgreSQL con la extensión pgvector para embeddings vectoriales:

```env

# Configuración específica
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=chatbot_password
POSTGRES_DB=chatbot_db

# Pool de conexiones
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DATABASE_ECHO=false

# Embeddings vectoriales
EMBEDDING_DIMENSION=1536
MAX_EMBEDDING_BATCH_SIZE=100
OPENAI_API_KEY=tu-openai-api-key
```

#### Configuración de PostgreSQL

**Opción 1: Docker (Recomendado)**
```bash
# Usar el docker-compose.yml incluido (ya configurado con pgvector)
docker-compose up -d db
```

**Opción 2: Instalación Local**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib postgresql-server-dev-all

# Instalar pgvector
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# macOS con Homebrew
brew install postgresql pgvector
```

**Crear base de datos manualmente:**
```sql
-- Conectar como superusuario
sudo -u postgres psql

-- Crear usuario y base de datos
CREATE USER chatbot_user WITH PASSWORD 'chatbot_password';
CREATE DATABASE chatbot_db OWNER chatbot_user;

-- Conectar a la nueva base de datos
\c chatbot_db

-- Crear extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;
```

## 🧠 Embeddings Vectoriales y Búsqueda Semántica

El proyecto incluye un sistema completo de embeddings vectoriales usando PostgreSQL + pgvector para búsqueda semántica avanzada.

### Características

- **Chunking Inteligente**: División automática de texto en chunks con overlap
- **Embeddings Vectoriales**: Soporte para dimensiones configurables (default: 1536)
- **Búsqueda de Similitud**: Búsqueda semántica usando distancia coseno
- **Procesamiento en Lotes**: Optimizado para procesar múltiples textos
- **API Completa**: Endpoints REST para todas las operaciones

### Ejemplos de Uso

#### 1. Crear Embeddings para una Pregunta

```bash
curl -X POST "http://localhost:8000/embeddings/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "123e4567-e89b-12d3-a456-426614174000",
    "text": "Este es el contexto de la pregunta que será procesado para generar embeddings vectoriales. El texto se dividirá automáticamente en chunks y se generarán embeddings para cada uno."
  }'
```

#### 2. Búsqueda Semántica

```bash
curl -X POST "http://localhost:8000/embeddings/search" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "¿Cómo funciona la autenticación en la aplicación?",
    "limit": 5,
    "similarity_threshold": 0.7
  }'
```

#### 3. Uso Programático

```python
from src.app.services.embedding_service import embedding_service

# Crear embeddings
embeddings = await embedding_service.create_embeddings_for_question(
    question_id="123e4567-e89b-12d3-a456-426614174000",
    text="Texto para procesar"
)

# Búsqueda de similitud
results = await embedding_service.search_by_text(
    query_text="¿Cómo funciona la autenticación?",
    limit=5,
    similarity_threshold=0.7
)

for chunk_embedding, similarity_score in results:
    print(f"Similitud: {similarity_score:.3f}")
    print(f"Texto: {chunk_embedding.chunk_text[:100]}...")
```

### Configuración de Rendimiento

Para mejor rendimiento con grandes volúmenes de datos, crear índices IVFFlat:

```sql
-- Crear índice después de tener al menos 1000 vectores
CREATE INDEX CONCURRENTLY idx_chunk_embeddings_vector 
ON chunk_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Índice para búsquedas por pregunta
CREATE INDEX CONCURRENTLY idx_chunk_embeddings_question_id 
ON chunk_embeddings (question_id);
```

### Monitoreo

```bash
# Estadísticas via API
curl -X GET "http://localhost:8000/embeddings/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Consultas SQL útiles
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(DISTINCT question_id) as unique_questions,
    AVG(chunk_size) as avg_chunk_size
FROM chunk_embeddings;
```

### Almacenamiento

Configuración para AWS S3:

```env
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=tu-access-key
MINIO_SECRET_KEY=tu-secret-key
MINIO_BUCKET_NAME=tu-bucket
MINIO_SECURE=true
```

### Email

Configuración para diferentes proveedores:

```env
# Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Outlook
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587

# SendGrid
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
```

## 🚀 Despliegue

### Variables de Entorno de Producción

```env
# Seguridad
SECRET_KEY=clave-super-segura-de-produccion
DEBUG=false

# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/chatbot

# CORS (ajustar según tu frontend)
ALLOWED_ORIGINS=https://tu-frontend.com,https://www.tu-frontend.com
```

### Nginx (Proxy Reverso)

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔍 Solución de Problemas

### ✅ **Problemas Resueltos en esta Configuración:**

1. **✅ Pydantic Settings**: Actualizado a `pydantic-settings` para compatibilidad con Pydantic v2
2. **✅ SQLAlchemy Async**: Configurado correctamente con `NullPool` para motores asíncronos
3. **✅ Campo metadata**: Renombrado a `chunk_metadata` para evitar conflictos con SQLAlchemy
4. **✅ pgvector Extension**: Configurada automáticamente en las migraciones
5. **✅ Docker Build**: Dockerfile corregido para incluir README.md

### Problemas Comunes y Soluciones

#### Error: "extension vector does not exist"
```bash
# Ya está resuelto automáticamente en las migraciones
# Si necesitas verificar manualmente:
docker-compose exec db psql -U chatbot_user -d chatbot_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

#### Error de Conexión a PostgreSQL
```bash
# Verificar servicios
docker-compose ps

# Ver logs
docker-compose logs db

# Reiniciar servicios si es necesario
docker-compose restart db
```

#### Error: "BaseSettings has been moved"
```bash
# Ya está resuelto - se instaló pydantic-settings
# Si aparece, instalar manualmente:
pip install pydantic-settings
```

#### Problemas de Rendimiento con Embeddings
```sql
-- Verificar uso de índices
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes 
WHERE relname = 'chunk_embeddings';

-- Reindexar si es necesario
REINDEX INDEX CONCURRENTLY idx_chunk_embeddings_vector;

-- Analizar tabla para estadísticas actualizadas
ANALYZE chunk_embeddings;
```

#### Migración desde SQLite
```bash
# 1. Hacer backup de datos existentes
cp chatbot.db chatbot_backup.db

# 2. Configurar PostgreSQL en .env
# 3. Ejecutar migraciones
alembic upgrade head

# 4. Migrar datos manualmente si es necesario
# (Los embeddings se regenerarán automáticamente)
```

### Mejores Prácticas

1. **Índices**: Crear índices IVFFlat después de tener al menos 1000 vectores
2. **Batch Processing**: Procesar embeddings en lotes para mejor rendimiento
3. **Monitoreo**: Usar `pg_stat_statements` para monitorear consultas lentas
4. **Backup**: Hacer backup regular con `pg_dump`
5. **Mantenimiento**: Ejecutar `VACUUM` y `ANALYZE` periódicamente

```bash
# Backup de PostgreSQL
docker-compose exec db pg_dump -U chatbot_user chatbot_db > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U chatbot_user chatbot_db < backup.sql
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial* - [tu-usuario](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- FastAPI por el excelente framework
- SQLAlchemy por el ORM potente y flexible
- PostgreSQL y pgvector por el soporte de embeddings vectoriales
- MinIO por el almacenamiento de archivos S3-compatible
- OpenAI por los modelos de embeddings
- La comunidad de Python por las librerías utilizadas

## 📞 Soporte

Si tienes preguntas o necesitas ayuda:

- 📧 Email: tu-email@ejemplo.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/APIChatBot/issues)
- 📖 Documentación: [Docs](https://github.com/tu-usuario/APIChatBot/wiki)

---

## 🎉 **Estado del Proyecto - LISTO PARA DESARROLLO**

### ✅ **Configuración Completada el 18 de Septiembre 2024:**

- **✅ Entorno de desarrollo**: Configurado y funcionando
- **✅ PostgreSQL 16 + pgvector**: Instalado y configurado
- **✅ Migraciones**: Aplicadas correctamente (5 tablas creadas)
- **✅ API FastAPI**: Funcionando en http://localhost:8000
- **✅ MinIO**: Configurado para almacenamiento de archivos
- **✅ Variables de entorno**: Configuradas en `.env`
- **✅ Dependencias**: Instaladas y actualizadas (pydantic-settings)
- **✅ Docker Compose**: Servicios funcionando correctamente

### 🚀 **Próximos Pasos Recomendados:**

1. **Configurar OpenAI API Key** para embeddings (opcional)
2. **Configurar SMTP** para emails de recuperación de contraseña
3. **Probar los endpoints** de la API con los docs en `/docs`
4. **Crear tu primer usuario** y categorías
5. **Experimentar con embeddings vectoriales**

### 📞 **Comandos de Inicio Rápido:**

```bash
# Todo en uno - iniciar desarrollo
docker-compose up -d db minio && source venv/bin/activate && python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 🔍 **Script de Verificación:**

Incluye un script para verificar que todo esté funcionando correctamente:

```bash
# Verificar que todos los servicios estén funcionando
source venv/bin/activate && python verify_setup.py
```

**Salida esperada:**
```
🔍 Verificando configuración de APIChatBot...
📅 Fecha: 2025-09-17 22:08:36
--------------------------------------------------
✅ API FastAPI: Funcionando correctamente
✅ PostgreSQL: Conectado - pgvector v0.8.1
✅ Base de datos: 5 tablas creadas
✅ MinIO: Funcionando correctamente
--------------------------------------------------
🎉 ¡Todos los servicios están funcionando correctamente!
🚀 Tu entorno de desarrollo está listo para usar
```

---

⭐ ¡No olvides dar una estrella al proyecto si te fue útil!
