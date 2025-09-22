import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.app.db.database import Base
from src.app.models.user import User
from src.app.config import settings
from src.app.utils.hashing import hash_password


async def create_default_user(session: AsyncSession):
    """Crea el usuario por defecto si no existe"""
    try:
        # Obtener credenciales desde variables de entorno
        default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@chatbot.local")
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        default_name = os.getenv("DEFAULT_ADMIN_NAME", "Administrador")
        default_role = os.getenv("DEFAULT_ADMIN_ROLE", "admin")

        # Verificar si el usuario ya existe
        result = await session.execute(
            "SELECT COUNT(*) FROM users WHERE email = :email",
            {"email": default_email}
        )
        user_exists = result.scalar() > 0

        if user_exists:
            print(f"ℹ️  Usuario por defecto {default_email} ya existe")
            return

        # Crear el usuario por defecto
        hashed_password = hash_password(default_password)
        new_user = User(
            email=default_email,
            name=default_name,
            hashed_password=hashed_password,
            role=default_role,
            is_active=True
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        print("✅ Usuario por defecto creado:")
        print(f"   📧 Email: {default_email}")
        print(f"   👤 Nombre: {default_name}")
        print(f"   🔑 Rol: {default_role}")
        print(f"   🆔 ID: {new_user.id}")

    except Exception as e:
        print(f"❌ Error al crear usuario por defecto: {e}")
        await session.rollback()
        raise


async def init_db():
    """Inicializa la base de datos y crea el usuario por defecto"""
    try:
        # Obtener URL de la base de datos desde configuración
        database_url = settings.get_database_url()
        print(f"Inicializando base de datos: {database_url}")

        # Crear motor asíncrono
        engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
        )

        # Crear todas las tablas
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Tablas de base de datos creadas exitosamente")

        # Crear sesión para operaciones de datos
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # Crear usuario por defecto
        async with async_session() as session:
            await create_default_user(session)

        print("🎉 Base de datos inicializada completamente!")
        await engine.dispose()

    except Exception as e:
        print(f"💥 Error al inicializar la base de datos: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())