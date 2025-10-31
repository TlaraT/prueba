#catalogo/admin.py
from django.contrib import admin
from django.shortcuts import render # <-- NUEVA IMPORTACIÓN
from django import forms
from .models import Categoria, Producto, Empleado
from import_export import resources
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget, Widget, ManyToManyWidget
from import_export.admin import ImportExportModelAdmin
from django.conf import settings
import os
from django.utils.text import slugify

# --- WIDGET PERSONALIZADO PARA MANEJAR IMÁGENES ---
class ImageWidget(Widget):
    """
    Widget personalizado para importar imágenes.
    Espera recibir solo el nombre del archivo (ej: 'taladro.jpg') en la celda.
    """
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None  # Si la celda está vacía, no hacemos nada

        # --- LÓGICA MODIFICADA ---
        # La ruta en el Excel ya debe ser relativa a la carpeta 'media'.
        # Por ejemplo: 'productos_imagenes/lijas/000001.webp'
        # Usamos slugify en cada parte de la ruta para asegurar consistencia
        # y evitar problemas de mayúsculas/minúsculas o espacios.
        parts = str(value).replace('\\', '/').split('/')
        slug_parts = [slugify(part) if '.' not in part else part for part in parts]
        relative_path = "/".join(slug_parts)

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

# --- NUEVO: Formulario para la acción de cambiar categoría ---
class CambiarCategoriaForm(forms.Form):
    # Campo para seleccionar la nueva categoría. Usamos ModelChoiceField para que se muestre como un <select>.
    categoria = forms.ModelChoiceField(queryset=Categoria.objects.all(), label="Seleccionar nueva categoría")

class ProductoAdmin(ImportExportModelAdmin):
    filter_horizontal = ('accesorios',)
    resource_class = ProductoResource
    list_display = ('nombre', 'precio', 'categoria', 'stock', 'es_mas_vendido')
    list_filter = ('categoria', 'es_mas_vendido', 'imagen')
    search_fields = ('nombre', 'categoria__nombre')
    ordering = ('nombre',)
    list_editable = ('precio', 'stock', 'es_mas_vendido')
    save_on_top = True
    actions = ['cambiar_categoria'] # <-- AÑADIMOS LA NUEVA ACCIÓN

    # --- NUEVA ACCIÓN PARA CAMBIAR CATEGORÍA EN LOTE ---
    def cambiar_categoria(self, request, queryset):
        """
        Acción de administrador para cambiar la categoría de múltiples productos seleccionados.
        """
        if 'apply' in request.POST:
            # El usuario ha enviado el formulario con la nueva categoría
            form = CambiarCategoriaForm(request.POST)
            if form.is_valid():
                nueva_categoria = form.cleaned_data['categoria']
                updated_count = queryset.update(categoria=nueva_categoria)
                self.message_user(request, f'{updated_count} productos han sido actualizados a la categoría "{nueva_categoria}".')
                return

        # Muestra la página intermedia para seleccionar la categoría.
        # Usamos django.shortcuts.render para renderizar la plantilla.
        form = CambiarCategoriaForm()
        return render(
            request,
            'admin/cambiar_categoria_intermedio.html',
            context={
                'title': 'Cambiar categoría de productos',
                'queryset': queryset,
                'opts': self.model._meta,
                'form': form, # Pasamos el objeto form directamente
                'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
            },
        )
    cambiar_categoria.short_description = "Cambiar categoría de productos seleccionados"
    

# --- PERSONALIZACIÓN DEL SITIO DE ADMINISTRACIÓN ---
admin.site.site_header = "Administración de Ferre Hogar Chuchin"
admin.site.site_title = "Portal de Administración"
admin.site.index_title = "Bienvenido al portal de gestión"

# --- NUEVO: Personalización del admin para Categorías ---
class CategoriaAdmin(admin.ModelAdmin):
    """
    Mejora la interfaz de administración para las categorías.
    """
    list_display = ('nombre', 'parent') # Muestra la categoría padre en la lista
    list_filter = ('parent',) # Permite filtrar por categoría padre
    search_fields = ('nombre', 'parent__nombre') # Permite buscar por nombre o nombre del padre
    ordering = ('nombre',)


# 3. Registros: Activamos todo en el panel de admin.
admin.site.register(Categoria, CategoriaAdmin) # Usamos la nueva clase personalizada
admin.site.register(Producto, ProductoAdmin)
