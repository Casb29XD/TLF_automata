import unittest
from app.automata import (
    dfa_placa, dfa_email, dfa_telefono, dfa_documento,
    dfa_url, dfa_fecha, dfa_password, extract_matches
)


class TestAutomataPlaca(unittest.TestCase):
    """Pruebas unitarias — AFD Placa Colombiana"""

    def test_placa_valida(self):
        self.assertTrue(dfa_placa.validate("ABC-1234"))
        self.assertTrue(dfa_placa.validate("ZXY-0000"))
        self.assertTrue(dfa_placa.validate("JKL-9999"))

    def test_placa_invalida(self):
        self.assertFalse(dfa_placa.validate("AB-1234"))    # Falta una letra
        self.assertFalse(dfa_placa.validate("ABCD-123"))   # Sobra letra
        self.assertFalse(dfa_placa.validate("ABC 1234"))   # Falta guion
        self.assertFalse(dfa_placa.validate("abc-1234"))   # Minúsculas
        self.assertFalse(dfa_placa.validate("ABC-12345"))  # Sobra un dígito
        self.assertFalse(dfa_placa.validate(""))           # Vacía


class TestAutomataEmail(unittest.TestCase):
    """Pruebas unitarias — AFD Correo Electrónico"""

    def test_email_valido(self):
        self.assertTrue(dfa_email.validate("usuario123@dominio.com"))
        self.assertTrue(dfa_email.validate("test.user-name@sub.domain.co"))
        self.assertTrue(dfa_email.validate("a@b.co"))

    def test_email_invalido(self):
        self.assertFalse(dfa_email.validate("user@.com"))        # Falta dominio
        self.assertFalse(dfa_email.validate("userdomain.com"))   # Falta @
        self.assertFalse(dfa_email.validate("user@domain"))      # Falta .tld
        self.assertFalse(dfa_email.validate("@domain.com"))      # Falta usuario
        self.assertFalse(dfa_email.validate(""))                 # Vacía


class TestAutomataTelefono(unittest.TestCase):
    """Pruebas unitarias — AFD Teléfono"""

    def test_telefono_valido(self):
        self.assertTrue(dfa_telefono.validate("3001234567"))        # 10 dígitos
        self.assertTrue(dfa_telefono.validate("+573001234567"))     # 12 dígitos int'l
        self.assertTrue(dfa_telefono.validate("+13001234567"))      # 11 dígitos int'l
        self.assertTrue(dfa_telefono.validate("320-123-4567"))      # Con guiones

    def test_telefono_internacional_con_espacio(self):
        """Formatos: +CC NNNNNNNNNN (código país + espacio + número)"""
        self.assertTrue(dfa_telefono.validate("+57 3124234234"))    # +2 espacio 10 dígitos
        self.assertTrue(dfa_telefono.validate("+1 5551234567"))     # +1 espacio 10 dígitos
        self.assertTrue(dfa_telefono.validate("+44 7911123456"))    # +2 espacio 10 dígitos

    def test_telefono_internacional_sin_espacio(self):
        """Formatos: +CCNNNNNNNN (código país pegado al número)"""
        self.assertTrue(dfa_telefono.validate("+5741245523"))       # +2 dígitos + 8 dígitos = 10
        self.assertTrue(dfa_telefono.validate("+573124234234"))     # +2 dígitos + 10 dígitos = 12
        self.assertTrue(dfa_telefono.validate("+15551234567"))      # +1 dígito + 10 dígitos = 11

    def test_telefono_invalido(self):
        self.assertFalse(dfa_telefono.validate("300123456"))   # 9 dígitos
        self.assertFalse(dfa_telefono.validate("+30012"))      # + y solo 5 dígitos
        self.assertFalse(dfa_telefono.validate(""))            # Vacía


class TestAutomataDocumento(unittest.TestCase):
    """Pruebas unitarias — AFD Documento de Identidad"""

    def test_documento_valido(self):
        self.assertTrue(dfa_documento.validate("123456"))       # 6 dígitos
        self.assertTrue(dfa_documento.validate("1234567890"))   # 10 dígitos
        self.assertTrue(dfa_documento.validate("12345678"))     # 8 dígitos

    def test_documento_invalido(self):
        self.assertFalse(dfa_documento.validate("12345"))       # 5 dígitos (< 6)
        self.assertFalse(dfa_documento.validate("12345678901")) # 11 dígitos (> 10)
        self.assertFalse(dfa_documento.validate("1234A6"))      # Con letra
        self.assertFalse(dfa_documento.validate(""))


class TestAutomataURL(unittest.TestCase):
    """Pruebas unitarias — AFD Dirección URL"""

    def test_url_valida(self):
        self.assertTrue(dfa_url.validate("https://www.example.com"))
        self.assertTrue(dfa_url.validate("http://sitio.co"))
        self.assertTrue(dfa_url.validate("https://www.example.com/path"))

    def test_url_invalida(self):
        self.assertFalse(dfa_url.validate("www.ejemplo.com"))    # Sin protocolo
        self.assertFalse(dfa_url.validate("ftp://algo.com"))     # Protocolo no soportado
        self.assertFalse(dfa_url.validate("https://"))           # Sin dominio
        self.assertFalse(dfa_url.validate(""))


class TestAutomataFecha(unittest.TestCase):
    """Pruebas unitarias — AFD Fecha"""

    def test_fecha_valida(self):
        self.assertTrue(dfa_fecha.validate("15/10/2026"))
        self.assertTrue(dfa_fecha.validate("2026-01-15"))
        self.assertTrue(dfa_fecha.validate("12-may-2026"))

    def test_fecha_invalida(self):
        self.assertFalse(dfa_fecha.validate("15102026"))   # Sin separador
        self.assertFalse(dfa_fecha.validate("15/10"))      # Incompleta
        self.assertFalse(dfa_fecha.validate(""))


class TestAutomataPassword(unittest.TestCase):
    """Pruebas unitarias — AFD Contraseña Segura"""

    def test_password_valida(self):
        self.assertTrue(dfa_password.validate("Abcde1@x"))       # Exactamente 8 chars
        self.assertTrue(dfa_password.validate("MyP@ssw0rd"))     # 10 chars
        self.assertTrue(dfa_password.validate("Str0ng!Pass"))    # 11 chars

    def test_password_invalida(self):
        self.assertFalse(dfa_password.validate("abc123"))        # Sin mayúscula ni especial, < 8
        self.assertFalse(dfa_password.validate("ABCDEFGH"))      # Sin minúscula, dígito ni especial
        self.assertFalse(dfa_password.validate("abcdefgh"))      # Sin mayúscula, dígito ni especial
        self.assertFalse(dfa_password.validate("Abcdefg1"))      # Sin especial
        self.assertFalse(dfa_password.validate("Ab1@"))          # Muy corta (4 chars)
        self.assertFalse(dfa_password.validate(""))


class TestExtractMatches(unittest.TestCase):
    """Pruebas del motor de extracción lineal"""

    def test_extract_multiple_patterns(self):
        texto = "El cliente juan@gmail.com maneja AAA-1111 y su teléfono es 3109876543."

        correos = extract_matches(dfa_email, texto)
        self.assertEqual(correos, ["juan@gmail.com"])

        placas = extract_matches(dfa_placa, texto)
        self.assertEqual(placas, ["AAA-1111"])

        telefonos = extract_matches(dfa_telefono, texto)
        self.assertEqual(telefonos, ["3109876543"])

    def test_extract_no_matches(self):
        texto = "Este texto no tiene patrones válidos para placas."
        placas = extract_matches(dfa_placa, texto)
        self.assertEqual(placas, [])

    def test_extract_urls(self):
        texto = "Visita https://ejemplo.com o http://otro.co para más info."
        urls = extract_matches(dfa_url, texto)
        self.assertIn("https://ejemplo.com", urls)
        self.assertIn("http://otro.co", urls)


if __name__ == '__main__':
    unittest.main()
