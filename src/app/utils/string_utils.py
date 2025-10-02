"""
String utils module
"""

import re
import unicodedata

def generate_slug(text: str) -> str:
    """
    Generates a slug from a text.
    Example: “research-project” -> “research-project”.
    """
    text = text.lower()

    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)

    return text.strip('-')
