# 🤖 APIChatBot - FastAPI ChatBot API

Una API moderna de chatbot construida con FastAPI que permite crear, gestionar y procesar preguntas con contexto de texto o archivos PDF, organizadas por categorías y con sistema de autenticación.

## 🚀 Características

- **🔐 Autenticación JWT**: Sistema completo de registro, login y gestión de usuarios
- **💬 Gestión de Preguntas**: Crear preguntas con contexto de texto o archivos PDF
- **📁 Sistema de Categorías**: Organización jerárquica de preguntas por categorías
- **📄 Procesamiento de PDFs**: Subida y procesamiento de archivos PDF como contexto
- **🔍 Búsqueda y Filtros**: Sistema avanzado de búsqueda y filtrado de preguntas
- **📊 Paginación**: Respuestas paginadas para mejor rendimiento
- **📧 Recuperación de Contraseña**: Sistema de reset de contraseña por email
- **👤 Gestión de Perfiles**: Actualización de perfiles de usuario
- **🗂️ Almacenamiento en la Nube**: Integración con MinIO para almacenamiento de archivos
- **🐳 Docker Ready**: Configuración completa para contenedores

## 🛠️ Tecnologías

- **Backend**: FastAPI 0.104+
- **Base de Datos**: SQLAlchemy 2.0 + SQLite/PostgreSQL
- **Autenticación**: JWT con python-jose
- **Almacenamiento**: MinIO (S3-compatible)
- **Email**: aiosmtplib para notificaciones
- **Migraciones**: Alembic
- **Testing**: pytest + pytest-asyncio
- **Contenedores**: Docker + Docker Compose

## 📋 Requisitos

- Python 3.11+
- Poetry (para gestión de dependencias)
- Docker y Docker Compose (opcional)
- MinIO o S3 (para almacenamiento de archivos)
- Servidor SMTP (para emails)

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

#### Opción B: Con pip y venv

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` basado en la plantilla:

```bash
cp env.template .env
```

Configura las siguientes variables en tu archivo `.env`:

```env
# Base de datos
DATABASE_URL=sqlite+aiosqlite:///./chatbot.db

# JWT
SECRET_KEY=tu-clave-secreta-super-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MinIO/S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=chatbot-files
MINIO_SECURE=false

# Email SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu-email@gmail.com
SMTP_PASSWORD=tu-contraseña-de-aplicación
SMTP_FROM_EMAIL=tu-email@gmail.com

# N8N Webhook (opcional)
N8N_WEBHOOK=http://localhost:5678/webhook/chatbot

# Configuración del servidor
HOST=0.0.0.0
PORT=8000
```

### 4. Configurar MinIO (Almacenamiento)

```bash
# Levantar MinIO con Docker Compose
docker-compose -f docker-compose.minio.yml up -d

# Acceder a la consola de MinIO
# URL: http://localhost:9001
# Usuario: minioadmin
# Contraseña: minioadmin
```

### 5. Inicializar la base de datos

```bash
# Ejecutar migraciones (crea todas las tablas automáticamente)
alembic upgrade head
```

## 🏃‍♂️ Ejecutar la aplicación

### Desarrollo

```bash
# Con Poetry
poetry run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Con Python directamente
python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción

```bash
# Con Gunicorn (recomendado para producción)
gunicorn src.app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Con Docker
docker build -t apichatbot .
docker run -p 8000:8000 apichatbot
```

La API estará disponible en: `http://localhost:8000`

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

# Acceder al contenedor
docker-compose exec api bash

# Parar servicios
docker-compose down
```

## 🔧 Configuración Avanzada

### Base de Datos

Por defecto usa SQLite, pero puedes configurar PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost:5432/chatbot_db
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
- SQLAlchemy por el ORM
- MinIO por el almacenamiento de archivos
- La comunidad de Python por las librerías utilizadas

## 📞 Soporte

Si tienes preguntas o necesitas ayuda:

- 📧 Email: tu-email@ejemplo.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/APIChatBot/issues)
- 📖 Documentación: [Docs](https://github.com/tu-usuario/APIChatBot/wiki)

---

⭐ ¡No olvides dar una estrella al proyecto si te fue útil!
