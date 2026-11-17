from django.db import models


class Proyecto(models.Model):
    """Modelo sencillo sobre el que se hacen las operaciones CRUD."""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.nombre
