# Taller: Peticiones HTTP en Django nativo

**Curso:** Desarrollo de aplicaciones Web I — 4E
**Presentado por** Luis Miguel Cantillo Sarmiento.
**Docente:** Jose Javier Torres Vanstrahlen

Endpoint CRUD construido **solo con Django**, usando una vista basada en clase (`View`) con los métodos `get()`, `post()`, `put()` y `delete()`.

---

## 1. Estructura del proyecto

```
taller/
├── manage.py
├── requirements.txt
├── config/                 # Proyecto Django
│   ├── settings.py         # Se registró la app "proyectos"
│   └── urls.py             # Incluye proyectos.urls bajo /api/
└── proyectos/              # Aplicación
    ├── models.py           # Modelo Proyecto
    ├── views.py            # ProyectoView (GET, POST, PUT, DELETE)
    ├── urls.py             # Rutas del endpoint (archivo creado)
    ├── admin.py
    ├── tests.py            # Pruebas de los 4 verbos
    └── migrations/
```

Archivos modificados o creados para el taller: `proyectos/views.py`, `proyectos/urls.py` (no existía, se creó), `proyectos/models.py`, `config/urls.py` y `config/settings.py`.

## 2. Cómo ejecutarlo

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Correr las pruebas automáticas:

```bash
python manage.py test
```

---

## 3. Verbos HTTP y su relación con CRUD

| Verbo HTTP | Operación CRUD | URL | Qué hace | Código de éxito |
|---|---|---|---|---|
| **GET** | **R**ead (leer) | `/api/proyectos/` | Lista todos los proyectos | 200 OK |
| **GET** | **R**ead (leer) | `/api/proyectos/<id>/` | Consulta un proyecto | 200 OK |
| **POST** | **C**reate (crear) | `/api/proyectos/` | Crea un proyecto nuevo | 201 Created |
| **PUT** | **U**pdate (actualizar) | `/api/proyectos/<id>/` | Modifica un proyecto existente | 200 OK |
| **DELETE** | **D**elete (eliminar) | `/api/proyectos/<id>/` | Elimina un proyecto | 200 OK |

Errores que maneja el endpoint: **400** (JSON inválido o falta `nombre`), **404** (el id no existe) y **405** (verbo no permitido, por ejemplo PATCH, o verbo usado en la URL equivocada).

### Casos de uso de cada verbo

**GET — leer información.** Se usa cuando el cliente solo quiere *consultar*: ver el catálogo de productos de una tienda, cargar el perfil de un usuario, buscar un proyecto por su id. Es un método **seguro** (no cambia nada en el servidor) e **idempotente** (pedirlo 1 o 100 veces da el mismo resultado). Por eso no lleva cuerpo; los filtros van en la URL (`?activo=true`).

**POST — crear un recurso nuevo.** Se usa para registrar un usuario, enviar un formulario de contacto, crear un pedido o, en este caso, un proyecto. Los datos van en el **cuerpo** de la petición (JSON). **No es idempotente**: si se envía dos veces, se crean dos registros. Se hace sobre la colección (`/api/proyectos/`) porque el id todavía no existe; lo asigna el servidor.

**PUT — actualizar un recurso existente.** Se usa para editar un registro ya creado: cambiar el nombre de un proyecto, actualizar la dirección de un cliente, marcar una tarea como inactiva. Va sobre un recurso específico (`/api/proyectos/5/`) y es **idempotente**: enviar la misma actualización varias veces deja el mismo estado final. En sentido estricto PUT reemplaza el recurso completo (PATCH sería la actualización parcial); en este taller el `put()` acepta campos parciales y deja igual los que no se envían, que es una simplificación común.

**DELETE — eliminar un recurso.** Se usa para borrar un proyecto, cancelar una cuenta o quitar un producto del carrito. Va sobre un recurso específico y también es **idempotente**: después de la primera vez el recurso ya no existe (la segunda petición devuelve 404, pero el estado del servidor es el mismo).

### ¿Cómo sabe Django qué método ejecutar?

`ProyectoView.as_view()` convierte la clase en una función que Django puede usar en `urls.py`. Cuando llega una petición, el método `dispatch()` de `View` mira `request.method` (por ejemplo `"PUT"`), lo pasa a minúsculas y llama al método de la clase con ese nombre (`put()`). Si el verbo no está definido o no aparece en `http_method_names`, llama a `http_method_not_allowed()`, que responde **405 Method Not Allowed**.

```
Petición HTTP ──► urls.py ──► ProyectoView.as_view() ──► dispatch()
                                                          ├─ GET    → get()
                                                          ├─ POST   → post()
                                                          ├─ PUT    → put()
                                                          ├─ DELETE → delete()
                                                          └─ otro   → 405
```

### Dos detalles importantes de Django nativo

1. **CSRF.** Django protege por defecto las peticiones POST, PUT y DELETE con un token CSRF pensado para formularios HTML. Un cliente de API (Postman, `fetch`, otra aplicación) no envía ese token, así que la petición sería rechazada con **403**. Por eso la vista se decora con `csrf_exempt`. En un proyecto real esto se reemplaza por otro mecanismo de autenticación (tokens, sesiones con el token CSRF en la cabecera, etc.).
2. **`request.POST` no sirve para JSON ni para PUT/DELETE.** Django solo llena `request.POST` cuando los datos vienen como formulario en una petición POST. Para recibir JSON (y siempre en PUT y DELETE) hay que leer `request.body` (bytes) y convertirlo con `json.loads()`. Eso hace la función `leer_json()` del `views.py`.

---

## 4. Código

### `proyectos/views.py` (resumen)

```python
# LIBRERIAS
import json
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from .models import Proyecto

# VISTA
@method_decorator(csrf_exempt, name="dispatch")
class ProyectoView(View):
    http_method_names = ["get", "post", "put", "delete"]

    def get(self, request, pk=None):      # Read
        ...
    def post(self, request, pk=None):     # Create
        ...
    def put(self, request, pk=None):      # Update
        ...
    def delete(self, request, pk=None):   # Delete
        ...
```

El parámetro `pk` es opcional (`pk=None`) porque la misma vista atiende dos URLs: la colección (`/proyectos/`, sin id) y el recurso (`/proyectos/<id>/`). Así, si alguien hace POST con id o PUT sin id, se responde 405 en vez de un error 500.

### `proyectos/urls.py`

```python
from django.urls import path
from .views import ProyectoView

urlpatterns = [
    path("proyectos/", ProyectoView.as_view(), name="proyectos"),
    path("proyectos/<int:pk>/", ProyectoView.as_view(), name="proyecto_detalle"),
]
```

### `config/urls.py`

```python
from django.urls import include, path
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("proyectos.urls")),
]
```

---

## 5. Módulos, funciones y decoradores de Django usados

### Módulos

| Módulo | Descripción |
|---|---|
| `django.views` | Contiene las vistas basadas en clase. De aquí se importa `View`. |
| `django.http` | Objetos de petición y respuesta (`HttpRequest`, `HttpResponse`, `JsonResponse`). |
| `django.urls` | Sistema de enrutamiento: asocia URLs con vistas (`path`, `include`). |
| `django.utils.decorators` | Utilidades para decoradores; de aquí sale `method_decorator`. |
| `django.views.decorators.csrf` | Decoradores relacionados con la protección CSRF (`csrf_exempt`). |
| `django.db.models` | ORM de Django: se usa para definir el modelo `Proyecto` y hacer consultas. |
| `django.forms.models` | Utilidades entre modelos y formularios; de aquí sale `model_to_dict`. |
| `json` (librería estándar de Python) | Convierte el texto JSON del cuerpo de la petición en diccionario (`json.loads`). No es externa: viene con Python. |

### Clases y funciones

| Elemento | Descripción |
|---|---|
| `View` | Clase base de todas las vistas basadas en clase. Su método `dispatch()` envía cada petición al método con el nombre del verbo HTTP (`get`, `post`, `put`, `delete`). |
| `View.as_view()` | Método de clase que convierte la vista en una función invocable para usarla en `path()`. |
| `View.dispatch()` | Recibe la petición y decide qué método ejecutar según `request.method`. |
| `View.http_method_names` | Lista de verbos que la vista acepta. Se limitó a los cuatro del taller; los demás responden 405. |
| `View.http_method_not_allowed()` | Devuelve la respuesta 405 cuando el verbo no está permitido. |
| `JsonResponse` | Subclase de `HttpResponse` que convierte un diccionario a JSON y pone la cabecera `Content-Type: application/json`. Su parámetro `status` define el código HTTP. Por defecto solo acepta diccionarios (`safe=True`); para devolver una lista directamente habría que pasar `safe=False`. |
| `request.method` | Atributo con el verbo de la petición (`"GET"`, `"POST"`, …). |
| `request.body` | Cuerpo crudo de la petición en bytes. Es la forma de leer JSON y los datos de PUT/DELETE. |
| `path()` | Define una ruta. Soporta convertidores como `<int:pk>`, que captura el id y lo pasa como argumento a la vista. |
| `include()` | Incluye las rutas de una aplicación dentro de las rutas del proyecto (`api/` + `proyectos/`). |
| `models.Model` | Clase base para definir modelos (tablas) en el ORM. |
| `Model.objects.all()` / `.get()` / `.create()` | Métodos del ORM para listar, buscar uno y crear registros. |
| `instancia.save()` / `instancia.delete()` | Guardan los cambios o eliminan el registro en la base de datos. |
| `Model.DoesNotExist` | Excepción que lanza `.get()` cuando no hay registro con ese id; se captura para responder 404. |
| `model_to_dict()` | Convierte una instancia de modelo en un diccionario, listo para enviarlo en un `JsonResponse`. |
| `json.loads()` | Convierte el texto JSON en un diccionario de Python. Si el JSON está mal formado lanza `json.JSONDecodeError` (se responde 400). |

### Decoradores

| Decorador | Descripción |
|---|---|
| `@csrf_exempt` | Desactiva la verificación del token CSRF para una vista. Sin él, Django rechaza con 403 los POST, PUT y DELETE hechos desde clientes de API. |
| `@method_decorator(decorador, name="dispatch")` | Adapta un decorador hecho para funciones (como `csrf_exempt`) para usarlo en una clase. Con `name="dispatch"` se aplica a `dispatch()`, que es por donde pasan todos los verbos, así queda aplicado a `get`, `post`, `put` y `delete` a la vez. |

Otros decoradores que investigué y que sirven para vistas **basadas en funciones** (no se usaron porque la vista es de clase, donde `http_method_names` cumple esa función):

| Decorador | Descripción |
|---|---|
| `@require_http_methods(["GET", "POST"])` | De `django.views.decorators.http`. Restringe una vista de función a ciertos verbos; los demás reciben 405. |
| `@require_GET`, `@require_POST` | Atajos del anterior para un solo verbo. |
| `@login_required` | De `django.contrib.auth.decorators`. Exige que el usuario haya iniciado sesión. En clases se usa con `method_decorator` o con `LoginRequiredMixin`. |

---

## 6. Pruebas con curl (o Postman)

Con el servidor corriendo (`python manage.py runserver`). Estas salidas son reales, obtenidas al probar el proyecto:

```bash
# CREATE (POST)
curl -X POST http://127.0.0.1:8000/api/proyectos/ \
     -H "Content-Type: application/json" \
     -d '{"nombre": "Tienda online", "descripcion": "Proyecto final"}'
# → 201 {"id": 1, "nombre": "Tienda online", "descripcion": "Proyecto final", "activo": true, ...}

# READ (GET)
curl http://127.0.0.1:8000/api/proyectos/
# → 200 {"proyectos": [{"id": 1, "nombre": "Tienda online", ...}]}

# UPDATE (PUT)
curl -X PUT http://127.0.0.1:8000/api/proyectos/1/ \
     -H "Content-Type: application/json" \
     -d '{"activo": false}'
# → 200 {"id": 1, "nombre": "Tienda online", ..., "activo": false, ...}

# DELETE
curl -X DELETE http://127.0.0.1:8000/api/proyectos/1/
# → 200 {"mensaje": "Proyecto 1 eliminado"}

# Recurso inexistente
curl http://127.0.0.1:8000/api/proyectos/1/
# → 404 {"error": "Proyecto no encontrado"}
```

> En Windows (CMD) se usan comillas dobles en `-d` escapando las internas: `-d "{\"nombre\": \"Tienda online\"}"`. En Postman: elegir el método, en *Body* → *raw* → *JSON*.

El archivo `proyectos/tests.py` tiene 8 pruebas automáticas (listar, consultar, 404, crear, validación 400, actualizar, eliminar y 405); todas pasan con `python manage.py test`.

---

## 7. Fuentes consultadas

1. Django Software Foundation. *Base views* (`View`, `dispatch`, `http_method_names`, `as_view`). Documentación de Django 6.1. https://docs.djangoproject.com/en/6.1/ref/class-based-views/base/
2. Django Software Foundation. *Introduction to class-based views* (manejo de verbos y decoración de vistas de clase con `method_decorator`). https://docs.djangoproject.com/en/6.1/topics/class-based-views/intro/
3. Django Software Foundation. *Request and response objects* (`request.method`, `request.body`, `JsonResponse`). https://docs.djangoproject.com/en/6.1/ref/request-response/
4. Django Software Foundation. *URL dispatcher* (`path`, `include`, convertidores de ruta). https://docs.djangoproject.com/en/6.1/topics/http/urls/
5. Django Software Foundation. *View decorators* (`require_http_methods`, `require_GET`, `require_POST`). https://docs.djangoproject.com/en/6.1/topics/http/decorators/
6. Django Software Foundation. *Cross Site Request Forgery protection* (`csrf_exempt`). https://docs.djangoproject.com/en/6.1/ref/csrf/
7. Django Software Foundation. *Making queries* (ORM: `all`, `get`, `create`, `save`, `delete`). https://docs.djangoproject.com/en/6.1/topics/db/queries/
8. Django Software Foundation. *Base views*, documentación en Read the Docs (versión 6.0.x). https://django.readthedocs.io/en/6.0.x/ref/class-based-views/base.html
9. MDN Web Docs. *HTTP request methods*. https://developer.mozilla.org/es/docs/Web/HTTP/Methods
10. IETF. *RFC 9110 – HTTP Semantics*, sección 9 (métodos, seguridad e idempotencia). https://www.rfc-editor.org/rfc/rfc9110#section-9
11. Python Software Foundation. *json — JSON encoder and decoder*. https://docs.python.org/3/library/json.html
