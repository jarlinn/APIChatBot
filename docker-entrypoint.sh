#!/bin/bash

# Docker entrypoint script para APIChatBot
set -e

echo "🚀 Iniciando APIChatBot..."

# Función para esperar a que un servicio esté disponible
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3

    echo "⏳ Esperando a que $service_name esté disponible en $host:$port..."

    while ! curl -f --connect-timeout 1 "http://$host:$port" >/dev/null 2>&1; do
        echo "   $service_name no está listo, esperando..."
        sleep 2
    done

    echo "✅ $service_name está disponible!"
}

# Esperar a MinIO si es una instancia local
if [[ "$MINIO_ENDPOINT" == localhost* ]] || [[ "$MINIO_ENDPOINT" == 127.0.0.1* ]]; then
    PROTOCOL="http"
    if [ "$MINIO_SECURE" = true ]; then
        PROTOCOL="https"
    fi
    echo "⏳ Esperando a que MinIO esté disponible en $MINIO_ENDPOINT"
    while ! curl -f --connect-timeout "$PROTOCOL:$MINIO_ENDPOINT/minio/health/live" >/dev/null 2>&1; do
        echo "   MinIO no está listo, esperando..."
        sleep 2
    done
    echo "✅ MinIO está disponible!"
fi

# Esperar a PostgreSQL si está configurado
if [[ "$DATABASE_URL" == *"postgresql"* ]]; then
    echo "⏳ Esperando a PostgreSQL..."
    while ! pg_isready -h db -p 5432 -U chatbot_user; do
        echo "   PostgreSQL no está listo, esperando..."
        sleep 2
    done
    echo "✅ PostgreSQL está disponible!"
fi

# Ejecutar migraciones de base de datos
echo "🔄 Ejecutando migraciones de base de datos..."
alembic upgrade head

# Crear bucket en MinIO si no existe y es instancia local
if [[ "$MINIO_ENDPOINT" == localhost* ]] || [[ "$MINIO_ENDPOINT" == 127.0.0.1* ]]; then
    if [ -n "$MINIO_BUCKET_NAME" ]; then
        echo "🗂️ Configurando bucket de MinIO..."
        python -c "
import asyncio
from src.app.services.storage_service import storage_service

async def setup_minio():
    try:
        await storage_service.create_bucket_if_not_exists()
        print('✅ Bucket de MinIO configurado correctamente')
    except Exception as e:
        print(f'⚠️ Error configurando MinIO: {e}')

asyncio.run(setup_minio())
" || echo "⚠️ No se pudo configurar MinIO automáticamente"
    fi
fi

echo "🎉 Configuración completada. Iniciando servidor..."

# Ejecutar el comando principal
exec "$@"
