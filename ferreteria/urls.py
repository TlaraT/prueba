from django.contrib import admin
from django.urls import path, include  # <-- Asegúrate de que 'include' esté importado
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ESTA ES LA LÍNEA QUE SOLUCIONA EL ERROR ---
    # Le dice al proyecto que para cualquier URL, busque las reglas
    # correspondientes dentro del archivo 'catalogo.urls'.
    path('', include('catalogo.urls')),

]

# Esto es necesario para que las imágenes de los productos se muestren
# correctamente mientras desarrollas tu sitio.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)