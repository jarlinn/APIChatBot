-- Script de inicialización para PostgreSQL con pgvector
-- Este script se ejecuta automáticamente cuando se crea el contenedor

-- Crear la extensión vector si no existe
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar que la extensión se instaló correctamente
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Configurar parámetros de PostgreSQL para mejor rendimiento con vectores
-- Estos comandos se ejecutan en el contexto de inicialización

-- Crear índices adicionales que pueden ser útiles
-- (Los índices específicos se crearán mediante las migraciones de Alembic)

-- Función para verificar la instalación de pgvector
CREATE OR REPLACE FUNCTION check_pgvector_installation()
RETURNS TEXT AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RETURN 'pgvector extension is successfully installed and ready to use!';
    ELSE
        RETURN 'ERROR: pgvector extension is not installed!';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Ejecutar la verificación
SELECT check_pgvector_installation();

-- Configurar algunos parámetros útiles para el trabajo con vectores
-- Nota: Algunos de estos requieren reinicio del servidor, por eso se configuran en el comando de docker

-- Crear un esquema específico para vectores si se necesita en el futuro
-- CREATE SCHEMA IF NOT EXISTS vectors;

-- Log de inicialización
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL with pgvector initialized successfully for APIChatBot';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user;
    RAISE NOTICE 'pgvector version: %', (SELECT extversion FROM pg_extension WHERE extname = 'vector');
END $$;
