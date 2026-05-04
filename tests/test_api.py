import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    # === Rutas de página ===
    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Motor", response.text)

    def test_formulario_page(self):
        response = self.client.get("/formulario")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Formulario", response.text)

    # === /api/patterns ===
    def test_api_patterns(self):
        response = self.client.get("/api/patterns")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        names = [p["name"] for p in data["patterns"]]
        self.assertIn("Correo Electrónico", names)
        self.assertIn("Contraseña Segura", names)

    # === /validate ===
    def test_validate_placa(self):
        response = self.client.post("/validate", data={"text": "XYZ-9876"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        self.assertEqual(response.json()["type"], "Placa Colombiana")

    def test_validate_fecha(self):
        response = self.client.post("/validate", data={"text": "12-may-2026"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        self.assertEqual(response.json()["type"], "Fecha")

    def test_validate_url(self):
        response = self.client.post("/validate", data={"text": "https://www.example.com/path"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        self.assertEqual(response.json()["type"], "Dirección URL")

    def test_validate_password(self):
        response = self.client.post("/validate", data={"text": "MyP@ssw0rd"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])
        self.assertEqual(response.json()["type"], "Contraseña Segura")

    def test_validate_fail(self):
        response = self.client.post("/validate", data={"text": "XYZ9876"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["valid"])

    # === /validate-field ===
    def test_validate_field_success(self):
        response = self.client.post(
            "/validate-field",
            data={"value": "test@email.com", "pattern": "Correo Electrónico"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])

    def test_validate_field_fail(self):
        response = self.client.post(
            "/validate-field",
            data={"value": "not-an-email", "pattern": "Correo Electrónico"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["valid"])

    def test_validate_field_bad_pattern(self):
        response = self.client.post(
            "/validate-field",
            data={"value": "anything", "pattern": "NoExiste"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["valid"])

    # === /extract ===
    def test_extract_route(self):
        texto = "Llamame al 3201234567 para verificar admin@empresa.com y entra a https://sitio.com el 25/12/2024"
        response = self.client.post("/extract", data={"text": texto})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        texts = [m["text"] for m in data["matches"]]
        self.assertIn("3201234567", texts)
        self.assertIn("admin@empresa.com", texts)
        self.assertIn("https://sitio.com", texts)
        self.assertIn("25/12/2024", texts)


if __name__ == '__main__':
    unittest.main()
