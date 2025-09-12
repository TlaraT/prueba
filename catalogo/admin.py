#catalogo/admin.py

from django.contrib import admin
from .models import Categoria, Producto, Empleado
from import_export import resources
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, Widget, ManyToManyWidget
from import_export.admin import ImportExportModelAdmin
from django.conf import settings
import os

# --- WIDGET PERSONALIZADO PARA MANEJAR IMÁGENES ---
class ImageWidget(Widget):
    """
    Widget personalizado para importar imágenes.
    Espera recibir solo el nombre del archivo (ej: 'taladro.jpg') en la celda.
    """
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None  # Si la celda está vacía, no hacemos nada

        # Construimos la ruta relativa que Django guardará en la base de datos
        relative_path = os.path.join('productos_imagenes', str(value))
        # Construimos la ruta completa para verificar que el archivo físico existe
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        if not os.path.exists(full_path):
            raise ValueError(f"La imagen '{value}' no se encontró. Súbela a la carpeta 'media/productos_imagenes/' antes de importar.")
        
        return relative_path

class EmpleadoResource(resources.ModelResource):
    class Meta:
        model = Empleado
        fields = ('nombre', 'puesto','email', 'telefono', 'horario_entrada', 'cumpleanos')
        import_id_fields = ('email',)  # Opcional: usa email como identificador único
class EmpleadoAdmin(ImportExportModelAdmin):
    resource_class = EmpleadoResource
    list_display = ('nombre', 'email', 'telefono', 'puesto', 'horario_entrada', 'cumpleanos')
    search_fields = ('nombre', 'email', 'puesto')
    
admin.site.register(Empleado, EmpleadoAdmin)






class ProductoResource(resources.ModelResource): 
    categoria = Field(
        column_name='categoria',
        attribute='categoria',
        widget=ForeignKeyWidget(Categoria, 'nombre')
    )
    imagen = Field(
        column_name='imagen',
        attribute='imagen',
        widget=ImageWidget()
    )
    # --- CAMPO AJUSTADO PARA MANEJAR REFACCIONES ---
    # La columna en el Excel se llamará 'refacciones', pero internamente
    # seguirá apuntando al campo 'accesorios' del modelo.
    refacciones = Field(
        column_name='refacciones',
        attribute='accesorios', # Esto no se cambia, es el nombre interno del campo.
        widget=ManyToManyWidget(Producto, field='nombre', separator=',')
    )

    class Meta:
        model = Producto
        fields = ('nombre', 'descripcion', 'precio', 'categoria', 'imagen', 'stock', 'es_mas_vendido', 'refacciones')
        import_id_fields = ('nombre',)  # Usa 'nombre' como identificador único
        skip_unchanged = True
        report_skipped = False
        create_missing_fk = True

class ProductoAdmin(ImportExportModelAdmin):
    filter_horizontal = ('accesorios',)
    resource_class = ProductoResource
    list_display = ('nombre', 'precio', 'categoria', 'stock', 'es_mas_vendido')
    list_filter = ('categoria', 'es_mas_vendido', 'imagen')
    search_fields = ('nombre', 'categoria__nombre')
    ordering = ('nombre',)
    list_editable = ('precio', 'stock', 'es_mas_vendido')
    save_on_top = True
    

# --- PERSONALIZACIÓN DEL SITIO DE ADMINISTRACIÓN ---
admin.site.site_header = "Administración de Ferre Hogar Chuchin"
admin.site.site_title = "Portal de Administración"
admin.site.index_title = "Bienvenido al portal de gestión"


# 3. Registros: Activamos todo en el panel de admin.
admin.site.register(Categoria)
admin.site.register(Producto, ProductoAdmin)
