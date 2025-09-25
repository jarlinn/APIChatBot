#!/usr/bin/env python3
"""
Script para crear un usuario administrador por defecto al inicializar la
base de datos. Valida si el usuario ya existe antes de crearlo.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.config import settings  # noqa: E402
from src.app.models.user import User  # noqa: E402
from src.app.utils.hashing import hash_password  # noqa: E402


class DefaultUserInitializer:
    """Clase para inicializar el usuario por defecto"""

    def __init__(self):
        self.engine = None
        self.async_session = None

    async def setup_database(self):
        """Configura la conexión a la base de datos"""
        try:
            # Usar la URL de la configuración
            database_url = settings.get_database_url()
            print(f"Conectando a la base de datos: {database_url}")

            self.engine = create_async_engine(
                database_url,
                echo=settings.database_echo,
                pool_size=5,
                max_overflow=10
            )

            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            print("✅ Conexión a la base de datos establecida")

        except Exception as e:
            print(f"❌ Error al conectar con la base de datos: {e}")
            raise

    async def user_exists(self, email: str) -> bool:
        """Verifica si un usuario ya existe por email"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    "SELECT COUNT(*) FROM users WHERE email = :email",
                    {"email": email}
                )
                count = result.scalar()
                return count > 0
        except Exception as e:
            print(f"❌ Error al verificar usuario existente: {e}")
            return False

    async def create_default_user(
        self, email: str, password: str, name: str = "Administrador",
        role: str = "admin"
    ) -> bool:
        """Crea el usuario por defecto si no existe"""
        try:
            # Verificar si el usuario ya existe
            if await self.user_exists(email):
                print(f"ℹ️  El usuario {email} ya existe, omitiendo creación")
                return True

            # Crear el usuario
            hashed_password = hash_password(password)

            async with self.async_session() as session:
                new_user = User(
                    email=email,
                    name=name,
                    hashed_password=hashed_password,
                    role=role,
                    is_active=True
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)

                print("✅ Usuario por defecto creado exitosamente:")
                print(f"   📧 Email: {email}")
                print(f"   👤 Nombre: {name}")
                print(f"   🔑 Rol: {role}")
                print(f"   🆔 ID: {new_user.id}")

                return True

        except Exception as e:
            print(f"❌ Error al crear usuario por defecto: {e}")
            return False

    async def close(self):
        """Cierra la conexión a la base de datos"""
        if self.engine:
            await self.engine.dispose()
            print("🔒 Conexión a la base de datos cerrada")


async def main():
    """Función principal del script"""
    print("🚀 Iniciando creación de usuario por defecto...")

    # Obtener credenciales del usuario por defecto desde configuración
    default_email = settings.default_admin_email
    default_password = settings.default_admin_password
    default_name = settings.default_admin_name
    default_role = settings.default_admin_role

    print("📋 Configuración del usuario por defecto:")
    print(f"   📧 Email: {default_email}")
    print(f"   👤 Nombre: {default_name}")
    print(f"   🔑 Rol: {default_role}")
    print(f"   🔐 Contraseña: {'*' * len(default_password)}")

    initializer = DefaultUserInitializer()

    try:
        # Configurar base de datos
        await initializer.setup_database()

        # Crear usuario por defecto
        success = await initializer.create_default_user(
            email=default_email,
            password=default_password,
            name=default_name,
            role=default_role
        )

        if success:
            print("🎉 Proceso completado exitosamente")
            return 0
        else:
            print("❌ Error en el proceso de creación")
            return 1

    except Exception as e:
        print(f"💥 Error crítico: {e}")
        return 1

    finally:
        await initializer.close()


if __name__ == "__main__":
    # Verificar que estemos en el directorio correcto
    if not Path("src/app").exists():
        print(
            "❌ Error: Este script debe ejecutarse desde el directorio "
            "raíz del proyecto"
        )
        sys.exit(1)

    # Ejecutar el script
    exit_code = asyncio.run(main())
    sys.exit(exit_code)