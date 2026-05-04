from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.automata import (
    dfa_placa, dfa_email, dfa_telefono, dfa_documento,
    dfa_url, dfa_fecha, dfa_password, extract_matches
)
import os

app = FastAPI(
    title="Motor de Reconocimiento AFD",
    description="Validación mediante Autómatas Finitos Deterministas"
)

# Configuración de rutas estáticas y plantillas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")
static_dir = os.path.join(BASE_DIR, "static")

# Crear los directorios si no existen al arrancar
os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Diccionario para seleccionar el autómata correcto
dfas = {
    "Placa Colombiana": dfa_placa,
    "Correo Electrónico": dfa_email,
    "Teléfono": dfa_telefono,
    "Documento de Identidad": dfa_documento,
    "Dirección URL": dfa_url,
    "Fecha": dfa_fecha,
    "Contraseña Segura": dfa_password,
}

# Mensajes de ayuda por tipo de patrón
PATTERN_HINTS = {
    "Placa Colombiana": "3 letras mayúsculas, guión, 4 dígitos (ej: ABC-1234)",
    "Correo Electrónico": "usuario@dominio.ext (ej: info@empresa.com)",
    "Teléfono": "10 dígitos o +código país (ej: 3001234567, +573001234567)",
    "Documento de Identidad": "Entre 6 y 10 dígitos (ej: 1234567890)",
    "Dirección URL": "http:// o https:// seguido de dominio (ej: https://sitio.com)",
    "Fecha": "DD/MM/YYYY, YYYY-MM-DD o mes textual (ej: 15/10/2026, enero-01-2026)",
    "Contraseña Segura": "Mín. 8 caracteres: 1 mayúscula, 1 minúscula, 1 dígito, 1 especial (@#$%^&*!_-.)",
}


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    """Renderiza la interfaz principal — Motor de Reconocimiento."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/formulario", response_class=HTMLResponse)
async def read_formulario(request: Request):
    """Renderiza la página del formulario interactivo personalizable."""
    return templates.TemplateResponse("formulario.html", {"request": request})


@app.get("/api/patterns")
async def get_patterns():
    """Devuelve la lista de patrones disponibles con sus pistas de formato."""
    return {
        "patterns": [
            {"name": name, "hint": PATTERN_HINTS[name]}
            for name in dfas
        ]
    }


@app.post("/validate")
async def validate_string(text: str = Form(...)):
    """
    Ruta para la validación en tiempo real.
    Itera sobre todos los patrones para identificar el tipo automáticamente.
    """
    if not text.strip():
        return {"valid": False, "text": text, "type": None}

    for name, automata in dfas.items():
        if automata.validate(text):
            return {"valid": True, "text": text, "type": name}

    return {"valid": False, "text": text, "type": None}


@app.post("/validate-field")
async def validate_field(value: str = Form(...), pattern: str = Form(...)):
    """
    Valida un campo individual contra un patrón AFD específico.
    Usado por el formulario interactivo.
    """
    if pattern not in dfas:
        return {"valid": False, "error": f"Patrón '{pattern}' no reconocido."}

    automata = dfas[pattern]
    is_valid = automata.validate(value) if value.strip() else False

    return {
        "valid": is_valid,
        "value": value,
        "pattern": pattern,
        "hint": PATTERN_HINTS[pattern],
    }


@app.post("/extract")
async def extract_from_text(text: str = Form(...)):
    """
    Ruta que extrae todas las coincidencias usando todos los AFD,
    retornando qué tipo de patrón es cada subcadena.
    """
    all_matches = []

    for name, automata in dfas.items():
        matches = extract_matches(automata, text)
        for m in matches:
            # Avoid duplicate matches with the exact same type and string
            match_obj = {"text": m, "type": name}
            if match_obj not in all_matches:
                all_matches.append(match_obj)

    return {"matches": all_matches, "count": len(all_matches)}
