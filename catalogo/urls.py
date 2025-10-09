# catalogo/urls.py
from django.urls import path
from . import views

# --- ESTA ES LA LÍNEA QUE SOLUCIONA EL ERROR ---
# Le da un "nombre" a este conjunto de URLs para que Django pueda encontrarlas.
app_name = 'catalogo'

urlpatterns = [
    # Ruta para la página de inicio
    path('', views.inicio, name='inicio'),
    
    # Ruta para la página principal del catálogo (la que muestra las categorías)
    path('catalogo/', views.catalogo, name='catalogo'),
    
    # Ruta para la página "Quiénes Somos"
    path('quienes_somos/', views.quienes_somos, name='quienes_somos'),
    
    # Ruta para ver los productos de una categoría específica
    path('catalogo/categoria/<int:categoria_id>/', views.categoria_detalle, name='categoria_detalle'),

    # Ruta para la página de contacto
    path('contacto/', views.contacto, name='contacto'), 
    # Ruta para ver los detalles de un producto específico
    path('producto/<int:producto_id>/', views.producto_detalle, name='producto_detalle'),

    # --- NUEVA RUTA PARA SUGERENCIAS DE BÚSQUEDA ---
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
]
  # --- IGNORE ---
