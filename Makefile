# Makefile para APIChatBot
.PHONY: help build up down logs restart clean rebuild migrate shell test

# Variables
COMPOSE_FILE = docker-compose.yml
SERVICE_API = api
SERVICE_MINIO = minio

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostrar esta ayuda
	@echo "$(GREEN)APIChatBot - Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Servicios disponibles:$(NC)"
	@echo "  - api: Aplicación FastAPI"
	@echo "  - minio: Almacenamiento de archivos"
	@echo ""

build: ## Construir las imágenes Docker
	@echo "$(GREEN)🔨 Construyendo imágenes...$(NC)"
	docker-compose build

up: ## Levantar todos los servicios
	@echo "$(GREEN)🚀 Levantando servicios...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Servicios iniciados!$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)MinIO Console: http://localhost:9001$(NC)"

down: ## Parar todos los servicios
	@echo "$(RED)🛑 Parando servicios...$(NC)"
	docker-compose down

logs: ## Ver logs de todos los servicios
	docker-compose logs -f

logs-api: ## Ver logs solo de la API
	docker-compose logs -f $(SERVICE_API)

logs-minio: ## Ver logs solo de MinIO
	docker-compose logs -f $(SERVICE_MINIO)

restart: ## Reiniciar todos los servicios
	@echo "$(YELLOW)🔄 Reiniciando servicios...$(NC)"
	docker-compose restart

restart-api: ## Reiniciar solo la API
	@echo "$(YELLOW)🔄 Reiniciando API...$(NC)"
	docker-compose restart $(SERVICE_API)

clean: ## Limpiar contenedores, redes e imágenes no utilizadas
	@echo "$(RED)🧹 Limpiando recursos Docker...$(NC)"
	docker-compose down -v --remove-orphans
	docker system prune -f

rebuild: ## Reconstruir y levantar servicios
	@echo "$(GREEN)🔄 Reconstruyendo servicios...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)✅ Servicios reconstruidos y iniciados!$(NC)"

migrate: ## Ejecutar migraciones de base de datos
	@echo "$(GREEN)🔄 Ejecutando migraciones...$(NC)"
	docker-compose exec $(SERVICE_API) alembic upgrade head

init-db: ## Inicializar base de datos con tablas y usuario por defecto
	@echo "$(GREEN)🗄️ Inicializando base de datos...$(NC)"
	docker-compose exec $(SERVICE_API) python src/app/db/init_db.py

init-user: ## Crear usuario administrador por defecto
	@echo "$(GREEN)👤 Creando usuario por defecto...$(NC)"
	docker-compose exec $(SERVICE_API) python scripts/init_default_user.py

init-db-local: ## Inicializar base de datos localmente
	@echo "$(GREEN)🗄️ Inicializando base de datos localmente...$(NC)"
	poetry run python src/app/db/init_db.py

init-user-local: ## Crear usuario por defecto localmente
	@echo "$(GREEN)👤 Creando usuario por defecto localmente...$(NC)"
	poetry run python scripts/init_default_user.py

shell: ## Acceder al shell del contenedor de la API
	@echo "$(GREEN)🐚 Accediendo al contenedor...$(NC)"
	docker-compose exec $(SERVICE_API) bash

shell-root: ## Acceder al shell como root
	@echo "$(GREEN)🐚 Accediendo al contenedor como root...$(NC)"
	docker-compose exec -u root $(SERVICE_API) bash

test: ## Ejecutar tests
	@echo "$(GREEN)🧪 Ejecutando tests...$(NC)"
	docker-compose exec $(SERVICE_API) pytest

dev: ## Modo desarrollo (reconstruir API y levantar con logs)
	@echo "$(GREEN)🔧 Iniciando modo desarrollo...$(NC)"
	docker-compose build $(SERVICE_API)
	docker-compose up -d
	docker-compose logs -f $(SERVICE_API)

status: ## Ver estado de los servicios
	@echo "$(GREEN)📊 Estado de los servicios:$(NC)"
	docker-compose ps

setup: ## Configuración inicial completa
	@echo "$(GREEN)⚙️ Configuración inicial...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creando archivo .env desde plantilla...$(NC)"; \
		cp docker.env.template .env; \
		echo "$(RED)⚠️ Configura las variables en .env antes de continuar$(NC)"; \
	fi
	docker-compose build
	docker-compose up -d
	@echo "$(GREEN)✅ Configuración completada!$(NC)"
	@echo "$(YELLOW)Recuerda configurar las variables de entorno en .env$(NC)"

backup: ## Crear backup de los volúmenes
	@echo "$(GREEN)💾 Creando backup...$(NC)"
	mkdir -p backups
	docker run --rm -v chatbot_api_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/api_data_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	docker run --rm -v chatbot_minio_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/minio_data_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "$(GREEN)✅ Backup completado en ./backups/$(NC)"

# Comandos de desarrollo
install: ## Instalar dependencias localmente
	@echo "$(GREEN)📦 Instalando dependencias...$(NC)"
	poetry install

run-local: ## Ejecutar la aplicación localmente
	@echo "$(GREEN)🏃 Ejecutando aplicación localmente...$(NC)"
	poetry run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

# Comandos de producción
prod-build: ## Construir para producción
	@echo "$(GREEN)🏭 Construyendo para producción...$(NC)"
	docker-compose -f docker-compose.yml build --no-cache

prod-up: ## Levantar en modo producción
	@echo "$(GREEN)🚀 Iniciando en modo producción...$(NC)"
	docker-compose -f docker-compose.yml up -d

# Comandos de monitoreo
health: ## Verificar salud de los servicios
	@echo "$(GREEN)🏥 Verificando salud de servicios...$(NC)"
	@curl -f http://localhost:8000/health && echo "$(GREEN)✅ API saludable$(NC)" || echo "$(RED)❌ API no responde$(NC)"
	@curl -f http://localhost:9000/minio/health/live && echo "$(GREEN)✅ MinIO saludable$(NC)" || echo "$(RED)❌ MinIO no responde$(NC)"

# Default target
.DEFAULT_GOAL := help
