"""Utils file for questions"""

from typing import Optional
import logging

from src.app.services.storage_service import storage_service

logger = logging.getLogger(__name__)



def delete_file_if_exists(context_file_path: Optional[str] = None) :
    if not context_file_path:
        logger.info("file not found")
        return
    try:
        if storage_service.file_exists(context_file_path):
            storage_service.delete_file(context_file_path)
            logger.info(f"PDF file deleted from service {context_file_path}")
        else:
            logger.info("file not found")
    except Exception as exc:
        logger.error(f"error trying delete PDF file: {str(exc)}")
        raise
    