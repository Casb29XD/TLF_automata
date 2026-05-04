"""
Módulo de conexión a MongoDB Atlas.
Expone las colecciones: formularios_col, preguntas_col, respuestas_col.
"""

import os
import string
import random
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Cargar variables de entorno desde .env (raíz del proyecto)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "Tlf")

# Conexión al cluster (lazy: se conecta al primer uso)
_client = MongoClient(MONGODB_URI) if MONGODB_URI else None
_db = _client[MONGODB_DATABASE] if _client is not None else None

# Colecciones
formularios_col = _db["Formularios"] if _db is not None else None
preguntas_col = _db["Preguntas"] if _db is not None else None
respuestas_col = _db["Respuestas"] if _db is not None else None


def generar_codigo(longitud=6):
    """
    Genera un código alfanumérico único de N caracteres (mayúsculas + dígitos).
    Verifica que no exista ya en la colección de formularios.
    """
    chars = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(random.choices(chars, k=longitud))
        # Verificar unicidad
        if formularios_col is None or formularios_col.find_one({"codigo": codigo}) is None:
            return codigo
