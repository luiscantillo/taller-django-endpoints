# LIBRERIAS
import json

from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Proyecto


# FUNCIONES AUXILIARES
def leer_json(request):
    """Convierte el cuerpo (request.body) de la petición en un diccionario.

    Django solo llena request.POST con formularios; para JSON, y para PUT y
    DELETE en cualquier caso, hay que leer y decodificar request.body a mano.
    """
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def serializar(proyecto):
    """Convierte una instancia del modelo en un diccionario apto para JSON."""
    datos = model_to_dict(proyecto)
    datos["fecha_creacion"] = proyecto.fecha_creacion.isoformat()
    return datos


# VISTA
@method_decorator(csrf_exempt, name="dispatch")
class ProyectoView(View):
    """Endpoint CRUD de proyectos.

    GET    /api/proyectos/        -> Read   (listar todos)
    GET    /api/proyectos/<pk>/   -> Read   (consultar uno)
    POST   /api/proyectos/        -> Create (crear)
    PUT    /api/proyectos/<pk>/   -> Update (actualizar)
    DELETE /api/proyectos/<pk>/   -> Delete (eliminar)
    """

    # Solo se aceptan estos verbos; cualquier otro responde 405.
    http_method_names = ["get", "post", "put", "delete"]

    def get(self, request, pk=None):
        if pk is None:
            proyectos = [serializar(p) for p in Proyecto.objects.all()]
            return JsonResponse({"proyectos": proyectos}, status=200)

        try:
            proyecto = Proyecto.objects.get(pk=pk)
        except Proyecto.DoesNotExist:
            return JsonResponse({"error": "Proyecto no encontrado"}, status=404)
        return JsonResponse(serializar(proyecto), status=200)

    def post(self, request, pk=None):
        if pk is not None:
            return JsonResponse({"error": "POST no lleva id en la URL"}, status=405)
        datos = leer_json(request)
        if datos is None:
            return JsonResponse({"error": "JSON inválido"}, status=400)
        if not datos.get("nombre"):
            return JsonResponse({"error": "Falta el campo 'nombre'"}, status=400)

        proyecto = Proyecto.objects.create(
            nombre=datos["nombre"],
            descripcion=datos.get("descripcion", ""),
            activo=datos.get("activo", True),
        )
        return JsonResponse(serializar(proyecto), status=201)

    def put(self, request, pk=None):
        if pk is None:
            return JsonResponse({"error": "PUT requiere el id en la URL"}, status=405)
        try:
            proyecto = Proyecto.objects.get(pk=pk)
        except Proyecto.DoesNotExist:
            return JsonResponse({"error": "Proyecto no encontrado"}, status=404)

        datos = leer_json(request)
        if datos is None:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        proyecto.nombre = datos.get("nombre", proyecto.nombre)
        proyecto.descripcion = datos.get("descripcion", proyecto.descripcion)
        proyecto.activo = datos.get("activo", proyecto.activo)
        proyecto.save()
        return JsonResponse(serializar(proyecto), status=200)

    def delete(self, request, pk=None):
        if pk is None:
            return JsonResponse({"error": "DELETE requiere el id en la URL"}, status=405)
        try:
            proyecto = Proyecto.objects.get(pk=pk)
        except Proyecto.DoesNotExist:
            return JsonResponse({"error": "Proyecto no encontrado"}, status=404)

        proyecto.delete()
        return JsonResponse({"mensaje": f"Proyecto {pk} eliminado"}, status=200)
