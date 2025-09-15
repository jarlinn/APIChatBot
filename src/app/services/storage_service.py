# src/app/services/storage_service.py
import os
import uuid
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException
import io


class StorageService:
    def __init__(self):
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_secure = (
            os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "chatbot-files")
        
        # Inicializar cliente MinIO
        self.client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access_key,
            secret_key=self.minio_secret_key,
            secure=self.minio_secure
        )
        
        # Crear bucket si no existe
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Crear el bucket si no existe"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' creado exitosamente")
        except S3Error as e:
            print(f"Error al crear/verificar bucket: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error de almacenamiento: {str(e)}"
            )
    
    async def upload_file(self, file: UploadFile, folder: str = "pdfs") -> str:
        """
        Subir archivo a MinIO/S3
        
        Args:
            file: Archivo a subir
            folder: Carpeta donde guardar el archivo
            
        Returns:
            str: Nombre del objeto en MinIO (path del archivo)
        """
        try:
            # Generar nombre único para el archivo
            file_extension = Path(file.filename).suffix if file.filename else ""
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            object_name = f"{folder}/{unique_filename}"
            
            # Leer el contenido del archivo
            file_content = await file.read()
            file_size = len(file_content)
            
            # Subir archivo a MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(file_content),
                length=file_size,
                content_type=(
                    file.content_type or "application/octet-stream"
                )
            )
            
            print(f"Archivo subido exitosamente: {object_name}")
            return object_name
            
        except S3Error as e:
            print(f"Error al subir archivo: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al subir archivo: {str(e)}"
            )
        except Exception as e:
            print(f"Error inesperado al subir archivo: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error interno: {str(e)}"
            )
    
    def get_file_url(self, object_name: str, expires_in_hours: int = 1) -> str:
        """
        Generar URL presignada para descargar archivo
        
        Args:
            object_name: Nombre del objeto en MinIO
            expires_in_hours: Horas de validez de la URL
            
        Returns:
            str: URL presignada para descargar
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(hours=expires_in_hours)
            )
            return url
        except S3Error as e:
            print(f"Error al generar URL: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al generar URL de descarga: {str(e)}"
            )
    
    def get_file_stream(self, object_name: str):
        """
        Obtener stream del archivo para descarga directa
        
        Args:
            object_name: Nombre del objeto en MinIO
            
        Returns:
            Stream del archivo
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return response
        except S3Error as e:
            print(f"Error al obtener archivo: {e}")
            raise HTTPException(
                status_code=404,
                detail="Archivo no encontrado"
            )
    
    def delete_file(self, object_name: str) -> bool:
        """
        Eliminar archivo de MinIO/S3
        
        Args:
            object_name: Nombre del objeto a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            print(f"Archivo eliminado: {object_name}")
            return True
        except S3Error as e:
            print(f"Error al eliminar archivo: {e}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        Verificar si un archivo existe en MinIO/S3
        
        Args:
            object_name: Nombre del objeto a verificar
            
        Returns:
            bool: True si el archivo existe
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except S3Error:
            return False

# Instancia global del servicio de almacenamiento
storage_service = StorageService()
