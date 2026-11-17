import json

from django.test import TestCase

from .models import Proyecto


class ProyectoViewTests(TestCase):
    """Prueba los cuatro verbos HTTP del endpoint /api/proyectos/."""

    def setUp(self):
        self.proyecto = Proyecto.objects.create(nombre="Inicial", descripcion="Demo")

    def test_get_lista(self):
        r = self.client.get("/api/proyectos/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["proyectos"]), 1)

    def test_get_detalle_y_404(self):
        r = self.client.get(f"/api/proyectos/{self.proyecto.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["nombre"], "Inicial")
        self.assertEqual(self.client.get("/api/proyectos/999/").status_code, 404)

    def test_post_crea(self):
        r = self.client.post(
            "/api/proyectos/",
            data=json.dumps({"nombre": "Nuevo", "descripcion": "Creado por POST"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Proyecto.objects.count(), 2)

    def test_post_valida(self):
        r = self.client.post("/api/proyectos/", data="{}", content_type="application/json")
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/api/proyectos/", data="no-json", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_put_actualiza(self):
        r = self.client.put(
            f"/api/proyectos/{self.proyecto.pk}/",
            data=json.dumps({"nombre": "Editado", "activo": False}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.nombre, "Editado")
        self.assertFalse(self.proyecto.activo)

    def test_delete_elimina(self):
        r = self.client.delete(f"/api/proyectos/{self.proyecto.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Proyecto.objects.exists())

    def test_verbo_no_permitido(self):
        r = self.client.patch(f"/api/proyectos/{self.proyecto.pk}/")
        self.assertEqual(r.status_code, 405)

    def test_url_equivocada(self):
        self.assertEqual(self.client.post(f"/api/proyectos/{self.proyecto.pk}/").status_code, 405)
        self.assertEqual(self.client.put("/api/proyectos/").status_code, 405)
        self.assertEqual(self.client.delete("/api/proyectos/").status_code, 405)
