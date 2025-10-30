# catalogo/context_processors.py
from django.conf import settings

def global_context(request):
    """
    Añade variables de configuración globales al contexto de todas las plantillas.
    """
    return {
        'CONTACTO_WHATSAPP': settings.CONTACTO_WHATSAPP,
    }