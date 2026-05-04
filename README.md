# Motor de Reconocimiento de Lenguajes Regulares

**Proyecto — Teoría de Lenguajes Formales**

> Búsqueda y validación de patrones en textos y sistemas interactivos mediante
> Autómatas Finitos Deterministas (AFD), sin uso de la librería `re` de Python.

---

## Objetivo General

Desarrollar una aplicación web que permita **detectar y validar patrones** dentro
de textos mediante **Autómatas Finitos Deterministas**, así como verificar la
entrada de datos en interfaces interactivas, asegurando que cumplan con criterios
sintácticos y estructurales previamente definidos.

---

## Arquitectura del Sistema

```
proyecto tlf/
├── app/
│   ├── automata.py       # Clase Automata (AFD) + 8 autómatas definidos
│   ├── main.py            # Servidor FastAPI (rutas y lógica)
│   ├── static/
│   │   ├── style.css      # Estilos (dark mode, glassmorphism)
│   │   └── script.js      # Lógica del frontend (validación tiempo real)
│   └── templates/
│       ├── index.html      # Página 1: Motor de reconocimiento
│       └── formulario.html # Página 2: Formulario interactivo dinámico
├── tests/
│   ├── test_automata.py   # Tests unitarios de los 8 AFD
│   └── test_api.py        # Tests de integración de la API
├── requirements.txt
└── README.md              # Este archivo
```

### Flujo de Datos

1. El usuario ingresa texto en la interfaz web.
2. El frontend envía la cadena al backend via `fetch()` (AJAX).
3. El backend procesa la cadena **símbolo por símbolo** usando el AFD correspondiente.
4. El resultado (aceptado/rechazado) se devuelve al frontend en tiempo real.

---

## Fundamentos Teóricos

### Definición Formal de un AFD

Un Autómata Finito Determinista se define formalmente como la quíntupla:

$$M = (Q, \Sigma, \delta, q_0, F)$$

Donde:
- **Q**: Conjunto finito de estados
- **Σ** (sigma): Alfabeto de entrada
- **δ** (delta): Función de transición `δ: Q × Σ → Q`
- **q₀**: Estado inicial (`q₀ ∈ Q`)
- **F**: Conjunto de estados de aceptación (`F ⊆ Q`)

### Implementación en Python

La clase `Automata` en `app/automata.py` implementa esta quíntupla:

```python
class Automata:
    def __init__(self, Q, sigma, delta, q0, F):
        self.Q = Q          # Conjunto de estados
        self.sigma = sigma  # Alfabeto
        self.delta = delta  # Función de transición (diccionario)
        self.q0 = q0        # Estado inicial
        self.F = set(F)     # Estados de aceptación
```

El método `validate(cadena)` recorre la cadena **carácter por carácter** sin
retroceder, siguiendo las transiciones definidas en `delta`. Si al consumir
toda la cadena el estado actual pertenece a `F`, la cadena es **aceptada**.

### Clases de Caracteres

Para simplificar las tablas de transición, se usan clases simbólicas que
agrupan caracteres con comportamiento equivalente:

| Clase | Descripción |
|-------|-------------|
| `<UPPERCASE_LETTERS>` | Letras mayúsculas (A-Z) |
| `<LOWERCASE_LETTERS>` | Letras minúsculas (a-z) |
| `<LETTERS>` | Cualquier letra |
| `<DIGITS>` | Dígitos (0-9) |
| `<ALPHANUM>` | Letras y dígitos |
| `<ALPHANUM_HYPHEN>` | Letras, dígitos y guión |
| `<SPECIALS>` | Caracteres especiales: `@#$%^&*!_-.` |
| `<URL_CHARS>` | Caracteres válidos en URLs |

---

## Autómatas Implementados

### 1. Placa Colombiana

**Formato**: 3 letras mayúsculas + guión + 4 dígitos (ej: `ABC-1234`)

| Estado | `<UPPERCASE_LETTERS>` | `-` | `<DIGITS>` |
|--------|-----------------------|-----|------------|
| q0 | q1 | — | — |
| q1 | q2 | — | — |
| q2 | q3 | — | — |
| q3 | — | q4 | — |
| q4 | — | — | q5 |
| q5 | — | — | q6 |
| q6 | — | — | q7 |
| q7 | — | — | **q8** ✓ |

---

### 2. Correo Electrónico

**Formato**: `usuario@dominio.ext` (ej: `info@empresa.com`)

| Estado | `<ALPHANUM>` | `<ALPHANUM_HYPHEN>` | `.` | `@` | `<LETTERS>` |
|--------|-------------|--------------------|----|-----|-------------|
| q0 | q1 | — | — | — | — |
| q1 | — | q1 | q_dot_user | q2 | — |
| q_dot_user | — | q1 | — | — | — |
| q2 | q3 | — | — | — | — |
| q3 | — | q3 | q_dot_domain | — | — |
| q_dot_domain | — | — | — | — | q4 |
| **q4** ✓ | — | — | q_dot_domain | — | q4 |

---

### 3. Número Telefónico

**Formatos aceptados**:
- 10 dígitos locales (ej: `3001234567`)
- Con separadores opcionales (ej: `320-123-4567`)
- Internacional con `+` (ej: `+573001234567`, `+1-555-123-4567`)

Genera dinámicamente estados para cada posición de dígito con estados
intermedios para separadores (`-` y espacio).

---

### 4. Documento de Identidad

**Formato**: Entre 6 y 10 dígitos consecutivos (ej: `1234567890`)

| Estado | `<DIGITS>` | Aceptación |
|--------|-----------|------------|
| q0→q5 | siguiente | No |
| q6→q10 | siguiente | **Sí** ✓ |

---

### 5. Dirección URL

**Formato**: `http://` o `https://` + dominio + path opcional

Reconoce el prefijo del protocolo carácter por carácter (`h`, `t`, `t`, `p`,
`s`?, `:`, `/`, `/`), luego el dominio con puntos, y opcionalmente un path.

---

### 6. Fecha

**Formatos aceptados**:
- Numérico: `DD/MM/YYYY`, `YYYY-MM-DD`
- Mixto: `12-may-2026`, `enero/01/2026`
- Separadores: `/` o `-`

Maneja 3 bloques separados, donde cada bloque puede ser numérico o textual.

---

### 7. Contraseña Segura

**Requisitos**: Mínimo 8 caracteres con al menos 1 mayúscula, 1 minúscula,
1 dígito y 1 carácter especial.

Utiliza **estados compuestos** `(flags, longitud)`:
- `flags`: bitmask de 4 bits (bit 0=mayúscula, 1=minúscula, 2=dígito, 3=especial)
- `longitud`: contador de 0 a 8+
- **Aceptación**: `flags = 15` (todos los bits) y `longitud ≥ 8`

Total de estados: 16 × 9 = 144 estados.

---

### 8. Monto de Dinero

**Formato**: Símbolo `$` seguido de dígitos, con separador de miles opcional
usando punto (ej: `$3000`, `$1.500.000`)

**Reglas**:
- El símbolo `$` es obligatorio al inicio.
- Debe haber al menos un dígito después del `$`.
- El punto (`.`) actúa como separador de miles y debe ir seguido de exactamente
  3 dígitos.
- Se permiten múltiples grupos de miles encadenados (ej: `$1.000.000`).

| Estado | `$` | `<DIGITS>` | `.` |
|--------|-----|-----------|-----|
| q0 | q_dollar | — | — |
| q_dollar | — | q_d1 | — |
| **q_d1** ✓ | — | q_d1 | q_dot |
| q_dot | — | q_m1 | — |
| q_m1 | — | q_m2 | — |
| q_m2 | — | q_m3 | — |
| **q_m3** ✓ | — | — | q_dot |

**Diagrama de transiciones**:

```
         $          <DIGITS>        .         <DIGITS>      <DIGITS>      <DIGITS>
(q0) --------→ (q_dollar) -----→ ((q_d1)) -----→ (q_dot) -----→ (q_m1) -----→ (q_m2) -----→ ((q_m3))
                                   ↑  ↑                                                          |
                                   |  └── <DIGITS> (loop)                                    . ──→ (q_dot)
                                   └── (loop)
```

---

## Motor de Extracción

La función `extract_matches(automata, texto)` recorre un texto largo de
izquierda a derecha buscando subcadenas aceptadas por el autómata:

1. Para cada posición `i`, intenta hacer coincidir desde `i` hacia adelante.
2. Registra la posición más larga donde el autómata estuvo en un estado de aceptación.
3. Si encontró coincidencia, la agrega y avanza `i` al final de la coincidencia.
4. Si no, avanza `i` un carácter.

**No usa** `re`, `find`, `split` ni ningún método de búsqueda de strings de alto nivel.

---

## Funcionalidades de la Aplicación

### Página 1: Motor de Reconocimiento

- **Validación en tiempo real**: El usuario escribe una cadena y el sistema
  detecta automáticamente si corresponde a algún patrón (con debounce de 200ms).
- **Extracción inteligente**: El usuario pega un bloque de texto largo y el
  motor recorre linealmente para encontrar y clasificar todas las coincidencias
  con badges de colores por tipo.

### Página 2: Formulario Interactivo

- **Constructor dinámico**: El usuario agrega campos al formulario eligiendo
  qué tipo de validación AFD aplica a cada uno.
- **Validación en tiempo real por campo**: Cada campo se valida contra su AFD
  asignado, mostrando feedback visual (✅/❌).
- **Medidor de fuerza de contraseña**: Barra visual para campos de contraseña.
- **Envío condicionado**: El botón de envío solo se habilita cuando todos los
  campos son válidos.

---

## Instalación y Ejecución

### Prerrequisitos
- Python 3.10+
- pip

### Instalación
```bash
cd "proyecto tlf"
pip install -r requirements.txt
```

### Ejecución
```bash
python -m uvicorn app.main:app --reload
```

Abrir en el navegador: `http://127.0.0.1:8000`

### Ejecutar Tests
```bash
python -m pytest tests/ -v
```

---

## Tabla de Casos de Prueba

### Placa Colombiana

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `ABC-1234` | ✅ Aceptada | Formato correcto |
| `ZXY-0000` | ✅ Aceptada | Formato correcto |
| `AB-1234` | ❌ Rechazada | Falta una letra |
| `ABC 1234` | ❌ Rechazada | Falta guión |
| `abc-1234` | ❌ Rechazada | Minúsculas no aceptadas |

### Correo Electrónico

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `usuario@dominio.com` | ✅ Aceptada | Formato válido |
| `test.user@sub.domain.co` | ✅ Aceptada | Con puntos y subdominios |
| `user@.com` | ❌ Rechazada | Falta nombre de dominio |
| `@domain.com` | ❌ Rechazada | Falta usuario |
| `user@domain` | ❌ Rechazada | Falta .tld |

### Número Telefónico

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `3001234567` | ✅ Aceptada | 10 dígitos locales |
| `+573001234567` | ✅ Aceptada | Internacional Colombia |
| `320-123-4567` | ✅ Aceptada | Con guiones |
| `300123456` | ❌ Rechazada | Solo 9 dígitos |

### Documento de Identidad

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `1234567890` | ✅ Aceptada | 10 dígitos |
| `123456` | ✅ Aceptada | 6 dígitos (mínimo) |
| `12345` | ❌ Rechazada | Solo 5 dígitos |
| `1234A6` | ❌ Rechazada | Contiene letra |

### Dirección URL

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `https://www.example.com` | ✅ Aceptada | HTTPS válido |
| `http://sitio.co` | ✅ Aceptada | HTTP válido |
| `www.ejemplo.com` | ❌ Rechazada | Sin protocolo |
| `ftp://algo.com` | ❌ Rechazada | Protocolo no soportado |

### Fecha

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `15/10/2026` | ✅ Aceptada | DD/MM/YYYY |
| `2026-01-15` | ✅ Aceptada | YYYY-MM-DD |
| `12-may-2026` | ✅ Aceptada | Con mes textual |
| `15102026` | ❌ Rechazada | Sin separador |

### Contraseña Segura

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `MyP@ssw0rd` | ✅ Aceptada | Cumple todos los requisitos |
| `Abcde1@x` | ✅ Aceptada | Exactamente 8 chars con todo |
| `abcdefgh` | ❌ Rechazada | Sin mayúscula, dígito ni especial |
| `Ab1@` | ❌ Rechazada | Muy corta (4 chars) |
| `Abcdefg1` | ❌ Rechazada | Sin carácter especial |

### Monto de Dinero

| Entrada | Resultado | Motivo |
|---------|-----------|--------|
| `$3000` | ✅ Aceptada | Monto sin separador |
| `$1.500` | ✅ Aceptada | Con separador de miles |
| `$1.000.000` | ✅ Aceptada | Millón con dos separadores |
| `$100.000` | ✅ Aceptada | Cien mil con separador |
| `$0` | ✅ Aceptada | Cero pesos |
| `3000` | ❌ Rechazada | Falta símbolo `$` |
| `$` | ❌ Rechazada | Sin dígitos |
| `$.500` | ❌ Rechazada | Punto sin dígitos previos |
| `$1.00` | ❌ Rechazada | Grupo de miles incompleto (2 dígitos) |
| `$1.` | ❌ Rechazada | Punto al final sin grupo |

---

## Tecnologías Utilizadas

| Tecnología | Propósito |
|-----------|-----------|
| **Python 3.10+** | Lenguaje principal |
| **FastAPI** | Framework web (backend) |
| **Uvicorn** | Servidor ASGI |
| **Jinja2** | Motor de plantillas HTML |
| **HTML/CSS/JS** | Interfaz de usuario |
| **Pytest** | Framework de pruebas |

### Restricción Técnica

**No se usa la librería `re` de Python** ni métodos de búsqueda de strings
de alto nivel. Toda la validación se realiza mediante la implementación manual
de Autómatas Finitos Deterministas que procesan las cadenas símbolo por símbolo.

---

## Conclusiones

- Se implementó exitosamente un motor de reconocimiento de lenguajes regulares
  basado en la teoría formal de autómatas.
- Los 8 autómatas implementados cubren patrones de uso real: placas vehiculares,
  correos electrónicos, teléfonos, documentos de identidad, URLs, fechas,
  contraseñas seguras y montos de dinero.
- La interfaz web ofrece validación en tiempo real y un constructor de
  formularios dinámico que permite al usuario personalizar los campos y sus
  validaciones.
- El procesamiento es estrictamente lineal (O(n)), siguiendo la definición
  formal de un AFD sin retroceso.
- Se verificó el correcto funcionamiento con casos de prueba automatizados
  que cubren escenarios válidos e inválidos para cada patrón.