import re
import unicodedata

def generate_slug(text: str) -> str:
    """
    Genera un slug a partir de un texto.
    Ejemplo: "Proyecto de Investigación" -> "proyecto-de-investigacion"
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Remover acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    
    # Reemplazar espacios con guiones
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Eliminar guiones al inicio y final
    return text.strip('-')
