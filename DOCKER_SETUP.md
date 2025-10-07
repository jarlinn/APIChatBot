# Docker Setup Guide

Esta guía proporciona instrucciones completas para configurar y ejecutar el proyecto ChatBot API usando Docker y Docker Compose.

## Requisitos Previos

- **Docker**: Versión 20.10 o superior
- **Docker Compose**: Versión 2.0 o superior
- **Sistema Operativo**: Linux, macOS o Windows con WSL2

### Verificar Instalación

```bash
# Verificar Docker
docker --version

# Verificar Docker Compose
docker-compose --version
```

## Comandos Básicos

### Iniciar Todos los Servicios (Desarrollo con Hot Reload)
```bash
docker-compose up -d
```
**Nota**: En modo desarrollo, los cambios en el código se reflejan automáticamente sin reconstruir la imagen.

### Iniciar Todos los Servicios (Producción)
```bash
docker-compose up --build -d
```

### Detener Todos los Servicios
```bash
docker-compose down

docker-compose down -v
```

### Reconstruir servicios
```bash
docker-compose build --no-cache
```

### Ver Logs de un Servicio
```bash
# Ver logs de la API
docker-compose logs -f api

# Ver logs de MinIO
docker-compose logs -f minio

# Ver logs de PostgreSQL
docker-compose logs -f db
```

### Reconstruir Imágenes
```bash
# Reconstruir la imagen de la API
docker-compose build api

# Reconstruir todas las imágenes
docker-compose build
```

### Acceder a Contenedores
```bash
# Acceder al contenedor de la API
docker-compose exec api bash

# Acceder al contenedor de PostgreSQL
docker-compose exec db psql -U chatbot_user -d chatbot_db
```

## Configuración de Entorno

### Variables de Entorno Requeridas

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

### Archivo de Plantilla

Hay un archivo `docker.env.template` que puedes copiar como base:

```bash
cp docker.env.template .env
```

## Acceso a Servicios

### API FastAPI
- **URL**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### MinIO (Almacenamiento de Archivos)
- **Consola Web**: http://localhost:9001
  - Usuario: `minioadmin`
  - Contraseña: `minioadmin`
- **API**: http://localhost:9000
- **Bucket**: `chatbot-files`

### PostgreSQL
- **Host**: localhost
- **Puerto**: 5432
- **Base de Datos**: `chatbot_db`
- **Usuario**: `chatbot_user`
- **Contraseña**: `chatbot_password`

## Comandos Útiles

### Ejecutar Migraciones de Base de Datos
```bash
# Dentro del contenedor de la API
docker-compose exec api alembic upgrade head

# O desde el host (si tienes Poetry instalado)
alembic upgrade head
```

### Ejecutar Tests
```bash
# Dentro del contenedor de la API
docker-compose exec api python -m pytest

# O desde el host
poetry run pytest
```

### Crear Usuario por Defecto
```bash
# Ejecutar script de inicialización
docker-compose exec api python scripts/init_default_user.py
```

### Ver Estado de los Servicios
```bash
docker-compose ps
```

### Limpiar Contenedores y Volúmenes (CUIDADO)
```bash
# Detener y eliminar contenedores
docker-compose down

# Detener, eliminar contenedores y volúmenes (elimina datos)
docker-compose down -v

# Limpiar imágenes no utilizadas
docker image prune -f
```

## Solución de Problemas

### Problema: Puerto ya en uso
```
Error: Port 8000 is already in use
```
**Solución**: Cambia el puerto en `docker-compose.yml` o libera el puerto.

### Problema: Error de conexión a PostgreSQL
```
Connection refused: db:5432
```
**Solución**:
- Verifica que el servicio `db` esté ejecutándose: `docker-compose ps`
- Espera a que el healthcheck pase (puede tomar hasta 1 minuto)
- Revisa logs: `docker-compose logs db`

### Problema: Error de permisos en MinIO
```
Access Denied
```
**Solución**: Verifica las credenciales en el archivo `.env` y que coincidan con las del `docker-compose.yml`.

### Problema: Migraciones no aplicadas
```
alembic: No such revision
```
**Solución**:
- Ejecuta `docker-compose exec api alembic current` para ver el estado
- Si es necesario, ejecuta `docker-compose exec api alembic stamp head`

### Problema: Contenedor no inicia
**Solución**:
- Revisa logs detallados: `docker-compose logs [servicio]`
- Verifica variables de entorno
- Reconstruye la imagen: `docker-compose build [servicio]`

### Problema: Memoria insuficiente
```
Out of memory
```
**Solución**: Aumenta la memoria asignada a Docker Desktop o libera recursos del sistema.

### Problema: Archivos no se copian correctamente
**Solución**: Asegúrate de que los archivos estén en el directorio correcto y reconstruye la imagen.

## Estructura de Servicios

```
chatbot-api (Proyecto)
├── api: Servicio principal FastAPI
├── db: Base de datos PostgreSQL con pgvector
├── minio: Almacenamiento de objetos
```

## Notas Adicionales

- Los volúmenes `postgres_data` y `minio_data` persisten los datos entre reinicios
- El servicio `api` espera a que `db` y `minio` estén listos antes de iniciar
- Los healthchecks aseguran que los servicios estén funcionando correctamente
- **Modo Desarrollo**: El código fuente se monta como volumen, permitiendo hot reload automático
- **Hot Reload**: Los cambios en archivos Python se detectan automáticamente y la aplicación se reinicia

## Desarrollo Local sin Docker

Si prefieres ejecutar localmente:

```bash
# Instalar dependencias
poetry install

# Configurar base de datos local
# Ejecutar PostgreSQL y MinIO localmente

# Ejecutar migraciones
alembic upgrade head

# Ejecutar la aplicación
poetry run uvicorn src.app.main:app --reload