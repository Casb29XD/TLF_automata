# Caracteres especiales aceptados para contraseñas
SPECIAL_CHARS = set("@#$%^&*!_-.")


class Automata:
    def __init__(self, Q, sigma, delta, q0, F):
        """
        Representación formal de un Autómata Finito Determinista (AFD).
        Q: Conjunto de estados (lista o set).
        sigma: Alfabeto (lista o set).
        delta: Función de transición, estructurada como un diccionario {estado: {simbolo_o_clase: estado_siguiente}}.
        q0: Estado inicial.
        F: Conjunto de estados de aceptación (set).
        """
        self.Q = Q
        self.sigma = sigma
        self.delta = delta
        self.q0 = q0
        self.F = set(F)

    def _get_transition(self, state, symbol):
        """Obtiene el siguiente estado dado un estado actual y un símbolo."""
        if state not in self.delta:
            return None
        
        transitions = self.delta[state]
        
        # Validar directamente si el símbolo exacto está en las transiciones
        if symbol in transitions:
            return transitions[symbol]
            
        # Validar usando clases de caracteres para simplificar la definición de delta
        # Orden: más específico primero para evitar ambigüedades
        for key, next_state in transitions.items():
            if key == '<UPPERCASE_LETTERS>' and symbol.isalpha() and symbol.isupper():
                return next_state
            if key == '<LOWERCASE_LETTERS>' and symbol.isalpha() and symbol.islower():
                return next_state
            if key == '<LETTERS>' and symbol.isalpha():
                return next_state
            if key == '<DIGITS>' and symbol.isdigit():
                return next_state
            if key == '<SPECIALS>' and symbol in SPECIAL_CHARS:
                return next_state
            if key == '<ALPHANUM>' and symbol.isalnum():
                return next_state
            if key == '<ALPHANUM_HYPHEN>' and (symbol.isalnum() or symbol == '-'):
                return next_state
            if key == '<URL_CHARS>' and (symbol.isalnum() or symbol in '-_.~:/?#[]@!$&\'()*+,;='):
                return next_state
            
        return None

    def validate(self, string):
        """
        Valida si una cadena completa es aceptada por el autómata.
        Procesa la cadena símbolo por símbolo de forma lineal.
        """
        if not string:
            return False
            
        current_state = self.q0
        for symbol in string:
            next_state = self._get_transition(current_state, symbol)
            # Si no hay transición definida para el símbolo actual, cae en sumidero implícito (rechazo)
            if next_state is None:
                return False
            current_state = next_state
        
        # La cadena es válida si termina en un estado de aceptación
        return current_state in self.F


def extract_matches(automata, text):
    """
    Recorre un texto largo linealmente para extraer todas las subcadenas
    que sean aceptadas por el autómata. No utiliza re, find, ni split.
    """
    matches = []
    i = 0
    n = len(text)
    
    while i < n:
        current_state = automata.q0
        j = i
        last_accepted_j = -1
        
        # Intentar coincidir desde el índice i hacia adelante
        while j < n:
            symbol = text[j]
            next_state = automata._get_transition(current_state, symbol)
            
            if next_state is None:
                break
                
            current_state = next_state
            
            if current_state in automata.F:
                last_accepted_j = j
                
            j += 1
            
        # Si encontramos un estado de aceptación en algún punto de esta traza
        if last_accepted_j != -1:
            match_str = text[i:last_accepted_j+1]
            matches.append(match_str)
            # Avanzar el puntero principal hasta el final de la coincidencia
            i = last_accepted_j + 1
        else:
            # Si no hubo coincidencia desde i, avanzar un carácter
            i += 1
            
    return matches


# ==========================================
# DEFINICIÓN DE LOS AUTÓMATAS REQUERIDOS
# ==========================================

# 1. AFD para Placas Colombianas (Ej: ABC-1234)
placa_Q = ['q0', 'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8']
placa_sigma = ['<UPPERCASE_LETTERS>', '<DIGITS>', '-']
placa_delta = {
    'q0': {'<UPPERCASE_LETTERS>': 'q1'},
    'q1': {'<UPPERCASE_LETTERS>': 'q2'},
    'q2': {'<UPPERCASE_LETTERS>': 'q3'},
    'q3': {'-': 'q4'},
    'q4': {'<DIGITS>': 'q5'},
    'q5': {'<DIGITS>': 'q6'},
    'q6': {'<DIGITS>': 'q7'},
    'q7': {'<DIGITS>': 'q8'}
}
placa_q0 = 'q0'
placa_F = ['q8']

dfa_placa = Automata(placa_Q, placa_sigma, placa_delta, placa_q0, placa_F)


# 2. AFD para Correos Electrónicos (básico)
email_Q = ['q0', 'q1', 'q_dot_user', 'q2', 'q3', 'q_dot_domain', 'q4']
email_sigma = ['<ALPHANUM>', '<ALPHANUM_HYPHEN>', '@', '.']
email_delta = {
    'q0': {'<ALPHANUM>': 'q1'},
    'q1': {
        '<ALPHANUM_HYPHEN>': 'q1',
        '.': 'q_dot_user',
        '@': 'q2'
    },
    'q_dot_user': {'<ALPHANUM_HYPHEN>': 'q1'},
    'q2': {'<ALPHANUM>': 'q3'},
    'q3': {
        '<ALPHANUM_HYPHEN>': 'q3',
        '.': 'q_dot_domain'
    },
    'q_dot_domain': {
        '<LETTERS>': 'q4'
    },
    'q4': {
        '<LETTERS>': 'q4',
        '.': 'q_dot_domain'
    }
}
email_q0 = 'q0'
email_F = ['q4']

dfa_email = Automata(email_Q, email_sigma, email_delta, email_q0, email_F)


# 3. AFD para Números Telefónicos
# Acepta separadores opcionales (guiones '-' y espacios ' ') entre dígitos.
# Formatos: 10 dígitos locales o '+' seguido de 7-15 dígitos (código país + número).
# Ejemplos válidos: 3201234567, 320-123-4567, +57 320 123 4567, +1-555-123-4567
# También acepta: +5741245523, +57 3124234234 (con/sin espacio después del código)

telefono_Q = []
telefono_sigma = ['<DIGITS>', '+', '-', ' ']
telefono_delta = {}

# --- Rama local: 10 dígitos con separadores opcionales ---
telefono_delta['q0'] = {'<DIGITS>': 'q1', '+': 'q_plus'}
telefono_Q.append('q0')

for i in range(1, 10):
    # Desde cada estado de dígito: siguiente dígito, o separador
    telefono_delta[f'q{i}'] = {'<DIGITS>': f'q{i+1}', '-': f'q{i}s', ' ': f'q{i}s'}
    # Estado separador: espera el siguiente dígito (o más separadores)
    telefono_delta[f'q{i}s'] = {'<DIGITS>': f'q{i+1}', '-': f'q{i}s', ' ': f'q{i}s'}
    telefono_Q.extend([f'q{i}', f'q{i}s'])
telefono_Q.append('q10')
telefono_delta['q10'] = {}  # Estado final, sin más transiciones

# --- Rama internacional: '+' seguido de 7 a 15 dígitos con separadores ---
# Cubre desde números cortos (+XX XXXXXXX) hasta largos (+XXX XXXXXXXXXXXX)
# Compatible con E.164: código país (1-3 dígitos) + número nacional (variable)
telefono_delta['q_plus'] = {'<DIGITS>': 'qp1'}
telefono_Q.append('q_plus')

for i in range(1, 15):
    telefono_delta[f'qp{i}'] = {'<DIGITS>': f'qp{i+1}', '-': f'qp{i}s', ' ': f'qp{i}s'}
    telefono_delta[f'qp{i}s'] = {'<DIGITS>': f'qp{i+1}', '-': f'qp{i}s', ' ': f'qp{i}s'}
    telefono_Q.extend([f'qp{i}', f'qp{i}s'])
telefono_Q.append('qp15')
telefono_delta['qp15'] = {}

telefono_q0 = 'q0'
# Estados de aceptación: 10 dígitos locales, o 7-15 dígitos después del '+'
telefono_F = ['q10', 'qp7', 'qp8', 'qp9', 'qp10', 'qp11', 'qp12', 'qp13', 'qp14', 'qp15']

dfa_telefono = Automata(telefono_Q, telefono_sigma, telefono_delta, telefono_q0, telefono_F)


# 4. AFD para Documentos (Cédulas u otros IDs)
# Acepta entre 6 y 10 dígitos consecutivos
doc_Q = [f'q{i}' for i in range(11)]
doc_sigma = ['<DIGITS>']
doc_delta = {}
for i in range(10):
    doc_delta[f'q{i}'] = {'<DIGITS>': f'q{i+1}'}
doc_q0 = 'q0'
doc_F = ['q6', 'q7', 'q8', 'q9', 'q10']

dfa_documento = Automata(doc_Q, doc_sigma, doc_delta, doc_q0, doc_F)


# 5. AFD para Direcciones URL
url_Q = ['q0', 'q_h', 'q_t1', 'q_t2', 'q_p', 'q_s', 'q_colon', 'q_slash1', 'q_slash2', 'q_domain', 'q_dot', 'q_tld', 'q_path']
url_sigma = ['<LETTERS>', '<ALPHANUM_HYPHEN>', '<URL_CHARS>', '.', ':', '/', 'h', 't', 'p', 's']
url_delta = {
    'q0': {'h': 'q_h'},
    'q_h': {'t': 'q_t1'},
    'q_t1': {'t': 'q_t2'},
    'q_t2': {'p': 'q_p'},
    'q_p': {'s': 'q_s', ':': 'q_colon'},
    'q_s': {':': 'q_colon'},
    'q_colon': {'/': 'q_slash1'},
    'q_slash1': {'/': 'q_slash2'},
    'q_slash2': {'<ALPHANUM_HYPHEN>': 'q_domain'},
    'q_domain': {'<ALPHANUM_HYPHEN>': 'q_domain', '.': 'q_dot'},
    'q_dot': {'<LETTERS>': 'q_tld'},
    'q_tld': {'<LETTERS>': 'q_tld', '.': 'q_dot', '/': 'q_path'},
    'q_path': {'<URL_CHARS>': 'q_path'}
}
url_q0 = 'q0'
url_F = ['q_tld', 'q_path']

dfa_url = Automata(url_Q, url_sigma, url_delta, url_q0, url_F)


# 6. AFD para Fechas
# Acepta formatos flexibles con '-' o '/' (ej: DD/MM/YYYY, YYYY-MM-DD, 12-may-2026)
fecha_delta = {
    'q0': {'<DIGITS>': 'q_d1', '<LETTERS>': 'q_l1'},
    
    # Bloque 1
    'q_d1': {'<DIGITS>': 'q_d2', '/': 'q_sep1', '-': 'q_sep1'},
    'q_d2': {'<DIGITS>': 'q_d3', '/': 'q_sep1', '-': 'q_sep1'},
    'q_d3': {'<DIGITS>': 'q_d4'},
    'q_d4': {'/': 'q_sep1', '-': 'q_sep1'},
    
    'q_l1': {'<LETTERS>': 'q_l1_loop', '/': 'q_sep1', '-': 'q_sep1'},
    'q_l1_loop': {'<LETTERS>': 'q_l1_loop', '/': 'q_sep1', '-': 'q_sep1'},
    
    # Separador 1
    'q_sep1': {'<DIGITS>': 'q_b2_d1', '<LETTERS>': 'q_b2_l1'},
    
    # Bloque 2
    'q_b2_d1': {'<DIGITS>': 'q_b2_d2', '/': 'q_sep2', '-': 'q_sep2'},
    'q_b2_d2': {'/': 'q_sep2', '-': 'q_sep2'},
    
    'q_b2_l1': {'<LETTERS>': 'q_b2_l1_loop', '/': 'q_sep2', '-': 'q_sep2'},
    'q_b2_l1_loop': {'<LETTERS>': 'q_b2_l1_loop', '/': 'q_sep2', '-': 'q_sep2'},
    
    # Separador 2
    'q_sep2': {'<DIGITS>': 'q_b3_d1', '<LETTERS>': 'q_b3_l1'},
    
    # Bloque 3
    'q_b3_d1': {'<DIGITS>': 'q_b3_d2'},
    'q_b3_d2': {'<DIGITS>': 'q_b3_d3'},
    'q_b3_d3': {'<DIGITS>': 'q_b3_d4'},
    'q_b3_d4': {},
    
    'q_b3_l1': {'<LETTERS>': 'q_b3_l1_loop'},
    'q_b3_l1_loop': {'<LETTERS>': 'q_b3_l1_loop'}
}
fecha_Q = list(fecha_delta.keys())
fecha_sigma = ['<DIGITS>', '<LETTERS>', '/', '-']
fecha_q0 = 'q0'
fecha_F = ['q_b3_d1', 'q_b3_d2', 'q_b3_d4', 'q_b3_l1', 'q_b3_l1_loop']

dfa_fecha = Automata(fecha_Q, fecha_sigma, fecha_delta, fecha_q0, fecha_F)


# 7. AFD para Contraseña Segura
# Requiere mínimo 8 caracteres con al menos: 1 mayúscula, 1 minúscula, 1 dígito, 1 especial.
# Estados compuestos: (flags, longitud) donde flags es un bitmask de 4 bits:
#   bit 0 = mayúscula vista, bit 1 = minúscula vista, bit 2 = dígito visto, bit 3 = especial visto
# Longitud se rastrea de 0 a 8+ (8 niveles antes de aceptación).

password_Q = []
password_delta = {}
password_F = []

for flags in range(16):
    for length in range(9):  # 0..8, donde 8 significa "8 o más"
        state = f"pw_{flags}_{length}"
        password_Q.append(state)
        password_delta[state] = {}

        # Si todos los flags están y longitud >= 8, es estado de aceptación
        if flags == 15 and length == 8:
            password_F.append(state)

        next_len = min(length + 1, 8)

        # Transición al consumir una mayúscula
        new_flags_upper = flags | 1
        password_delta[state]['<UPPERCASE_LETTERS>'] = f"pw_{new_flags_upper}_{next_len}"

        # Transición al consumir una minúscula
        new_flags_lower = flags | 2
        password_delta[state]['<LOWERCASE_LETTERS>'] = f"pw_{new_flags_lower}_{next_len}"

        # Transición al consumir un dígito
        new_flags_digit = flags | 4
        password_delta[state]['<DIGITS>'] = f"pw_{new_flags_digit}_{next_len}"

        # Transición al consumir un especial
        new_flags_special = flags | 8
        password_delta[state]['<SPECIALS>'] = f"pw_{new_flags_special}_{next_len}"

password_q0 = 'pw_0_0'

dfa_password = Automata(password_Q, ['<UPPERCASE_LETTERS>', '<LOWERCASE_LETTERS>', '<DIGITS>', '<SPECIALS>'],
                        password_delta, password_q0, password_F)
