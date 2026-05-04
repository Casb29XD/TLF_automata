from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.automata import (
    dfa_placa, dfa_email, dfa_telefono, dfa_documento,
    dfa_url, dfa_fecha, dfa_password, dfa_dinero, extract_matches
)
from app.db import formularios_col, preguntas_col, respuestas_col, generar_codigo
from bson import ObjectId
from datetime import datetime, timezone
import os
import json

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
    "Monto de Dinero": dfa_dinero,
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
    "Monto de Dinero": "Símbolo $ + dígitos, separador de miles con punto (ej: $3000, $1.500.000)",
}


# ========================================
# PÁGINAS
# ========================================

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    """Renderiza la interfaz principal — Motor de Reconocimiento."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/formulario", response_class=HTMLResponse)
async def read_formulario(request: Request):
    """Renderiza la página del formulario interactivo personalizable."""
    return templates.TemplateResponse("formulario.html", {"request": request})


# ========================================
# API — MOTOR DE RECONOCIMIENTO
# ========================================

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


@app.get("/health")
async def health_check():
    """Verifica la salud de la aplicación y la conexión a la base de datos."""
    try:
        if formularios_col is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "database": "disconnected", "error": "No connection string"}
            )
        
        # Intentar un ping real
        formularios_col.database.client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "error", "message": str(e)}
        )


# ========================================
# API — FORMULARIOS (CRUD con MongoDB)
# ========================================

def _check_db():
    """Verifica que la conexión a la base de datos esté disponible."""
    if formularios_col is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Base de datos no disponible. Verifica la configuración de MongoDB."}
        )
    return None


@app.post("/api/formularios")
async def crear_formulario(request: Request):
    """
    Crea un nuevo formulario con sus preguntas.
    Body JSON: { titulo, descripcion, contrasena, preguntas: [{etiqueta, patron}] }
    Devuelve el código único generado.
    """
    db_error = _check_db()
    if db_error:
        return db_error

    body = await request.json()
    titulo = body.get("titulo", "").strip()
    descripcion = body.get("descripcion", "").strip()
    contrasena = body.get("contrasena", "").strip()
    preguntas = body.get("preguntas", [])

    # Validaciones básicas
    if not titulo:
        return JSONResponse(status_code=400, content={"error": "El título es obligatorio."})
    if not contrasena:
        return JSONResponse(status_code=400, content={"error": "La contraseña es obligatoria."})
    if not preguntas or len(preguntas) == 0:
        return JSONResponse(status_code=400, content={"error": "Debe haber al menos una pregunta."})

    # Validar que cada pregunta tenga un patrón AFD válido
    for p in preguntas:
        if p.get("patron") not in dfas:
            return JSONResponse(
                status_code=400,
                content={"error": f"Patrón '{p.get('patron')}' no reconocido."}
            )

    # Generar código único
    codigo = generar_codigo()

    # Insertar formulario
    form_doc = {
        "codigo": codigo,
        "titulo": titulo,
        "descripcion": descripcion,
        "contrasena": contrasena,
        "creado_en": datetime.now(timezone.utc),
    }
    result = formularios_col.insert_one(form_doc)
    form_id = result.inserted_id

    # Insertar preguntas
    for i, p in enumerate(preguntas):
        preguntas_col.insert_one({
            "formulario_id": form_id,
            "etiqueta": p.get("etiqueta", f"Campo {i + 1}"),
            "patron": p["patron"],
            "orden": i + 1,
        })

    return {"codigo": codigo, "titulo": titulo, "mensaje": "Formulario creado exitosamente."}


@app.get("/api/formularios/{codigo}")
async def obtener_formulario(codigo: str):
    """
    Obtiene un formulario y sus preguntas por código.
    No requiere contraseña (es público para responder).
    """
    db_error = _check_db()
    if db_error:
        return db_error

    formulario = formularios_col.find_one({"codigo": codigo.upper()})
    if not formulario:
        return JSONResponse(status_code=404, content={"error": "Formulario no encontrado."})

    # Obtener preguntas ordenadas
    preguntas = list(
        preguntas_col.find({"formulario_id": formulario["_id"]}).sort("orden", 1)
    )

    return {
        "codigo": formulario["codigo"],
        "titulo": formulario["titulo"],
        "descripcion": formulario.get("descripcion", ""),
        "preguntas": [
            {
                "id": str(p["_id"]),
                "etiqueta": p["etiqueta"],
                "patron": p["patron"],
                "hint": PATTERN_HINTS.get(p["patron"], ""),
                "orden": p["orden"],
            }
            for p in preguntas
        ],
    }


@app.post("/api/formularios/{codigo}/respuestas")
async def guardar_respuesta(codigo: str, request: Request):
    """
    Guarda una respuesta a un formulario.
    Body JSON: { datos: [{pregunta_id, valor}] }
    Valida cada campo contra su AFD correspondiente antes de guardar.
    """
    db_error = _check_db()
    if db_error:
        return db_error

    formulario = formularios_col.find_one({"codigo": codigo.upper()})
    if not formulario:
        return JSONResponse(status_code=404, content={"error": "Formulario no encontrado."})

    body = await request.json()
    datos = body.get("datos", [])

    if not datos:
        return JSONResponse(status_code=400, content={"error": "No se enviaron datos."})

    # Validar cada campo contra su AFD
    errores = []
    datos_validados = []

    for d in datos:
        pregunta_id = d.get("pregunta_id")
        valor = d.get("valor", "").strip()

        # Buscar la pregunta
        try:
            pregunta = preguntas_col.find_one({"_id": ObjectId(pregunta_id)})
        except Exception:
            errores.append({"pregunta_id": pregunta_id, "error": "ID de pregunta inválido."})
            continue

        if not pregunta:
            errores.append({"pregunta_id": pregunta_id, "error": "Pregunta no encontrada."})
            continue

        # Validar con el AFD
        patron = pregunta["patron"]
        if patron in dfas:
            automata = dfas[patron]
            if not automata.validate(valor):
                errores.append({
                    "pregunta_id": pregunta_id,
                    "etiqueta": pregunta["etiqueta"],
                    "error": f"El valor '{valor}' no es válido para {patron}.",
                })
                continue

        datos_validados.append({
            "pregunta_id": ObjectId(pregunta_id),
            "etiqueta": pregunta["etiqueta"],
            "patron": patron,
            "valor": valor,
        })

    if errores:
        return JSONResponse(status_code=400, content={"error": "Hay campos inválidos.", "errores": errores})

    # Guardar respuesta
    respuestas_col.insert_one({
        "formulario_id": formulario["_id"],
        "datos": datos_validados,
        "respondido_en": datetime.now(timezone.utc),
    })

    return {"mensaje": "Respuesta guardada exitosamente.", "campos": len(datos_validados)}


@app.post("/api/formularios/{codigo}/respuestas/ver")
async def ver_respuestas(codigo: str, request: Request):
    """
    Lista todas las respuestas de un formulario.
    Requiere contraseña del creador para ver las respuestas.
    Body JSON: { contrasena: "..." }
    """
    db_error = _check_db()
    if db_error:
        return db_error

    formulario = formularios_col.find_one({"codigo": codigo.upper()})
    if not formulario:
        return JSONResponse(status_code=404, content={"error": "Formulario no encontrado."})

    body = await request.json()
    contrasena = body.get("contrasena", "")

    if contrasena != formulario.get("contrasena", ""):
        return JSONResponse(status_code=403, content={"error": "Contraseña incorrecta."})

    # Obtener respuestas
    respuestas = list(
        respuestas_col.find({"formulario_id": formulario["_id"]}).sort("respondido_en", -1)
    )

    # Obtener preguntas para referencia
    preguntas = list(
        preguntas_col.find({"formulario_id": formulario["_id"]}).sort("orden", 1)
    )

    return {
        "titulo": formulario["titulo"],
        "total_respuestas": len(respuestas),
        "preguntas": [
            {"etiqueta": p["etiqueta"], "patron": p["patron"]}
            for p in preguntas
        ],
        "respuestas": [
            {
                "respondido_en": r["respondido_en"].isoformat() if r.get("respondido_en") else "",
                "datos": [
                    {"etiqueta": d.get("etiqueta", ""), "valor": d.get("valor", "")}
                    for d in r.get("datos", [])
                ],
            }
            for r in respuestas
        ],
    }
