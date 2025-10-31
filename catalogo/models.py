# catalogo/models.py

from django.db import models
# --- NUEVAS IMPORTACIONES ---
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
# --- NUEVAS IMPORTACIONES PARA LA SEÑAL ---
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.conf import settings

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    puesto = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    horario_entrada = models.TimeField()
    cumpleanos = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    # --- NUEVO CAMPO PARA SUBCATEGORÍAS ---
    # Este campo permite que una categoría tenga una "Categoría Padre".
    # Si es nulo, es una categoría principal.
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategorias',
        verbose_name='Categoría Padre'
    )

    class Meta:
        # Ordena las categorías alfabéticamente para una mejor visualización en el admin.
        ordering = ('nombre',)
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        # Mejora la visualización en el admin para mostrar la jerarquía. Ej: "Mezcladoras > De Baño"
        return f"{self.parent.nombre} > {self.nombre}" if self.parent else self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=800)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    # Cambiado a SET_NULL para evitar borrados en cascada. Si se borra una categoría,
    # los productos asociados no se eliminarán, solo se quedarán sin categoría.
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='productos')
    imagen = models.ImageField(upload_to='productos_imagenes/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    es_mas_vendido = models.BooleanField(default=False)
    
    # --- CAMPO AÑADIDO PARA RELACIONAR PRODUCTOS ---
    # Este es el campo que faltaba y que causa el error.
    accesorios = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False, 
        related_name='producto_principal',
        verbose_name="Refacciones"  # <-- AÑADIMOS ESTO
    )
    
    def __str__(self):
        return self.nombre
    
    # --- MÉTODO AÑADIDO PARA URL CANÓNICA ---
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('catalogo:producto_detalle', args=[str(self.id)])

    # --- MÉTODO SAVE MODIFICADO PARA CONVERTIR IMÁGENES A WEBP ---
    def save(self, *args, **kwargs):
        # --- NUEVA LÓGICA PARA EVITAR DUPLICADOS EN IMPORTACIÓN ---
        # Si el campo 'imagen' tiene un valor y no es un archivo subido (es decir, es una cadena de texto
        # de la importación), y ya es un archivo .webp, no hacemos nada y guardamos directamente.
        # Esto evita que el proceso de conversión se ejecute sobre imágenes que ya están en el servidor.
        if self.imagen and not hasattr(self.imagen.file, 'content_type') and str(self.imagen.name).endswith('.webp'):
            super().save(*args, **kwargs)
            return

        # Primero, verificamos si el objeto ya existe en la BD para comparar la imagen.
        if self.pk:
            try:
                old_instance = Producto.objects.get(pk=self.pk)
                # Si la imagen no ha cambiado, simplemente guardamos y salimos.
                if old_instance.imagen == self.imagen:
                    super().save(*args, **kwargs)
                    return
            except Producto.DoesNotExist:
                # Esto ocurre si el objeto se está creando, así que continuamos.
                pass

        # Si llegamos aquí, es un producto nuevo o la imagen ha sido actualizada.
        # Procedemos a la conversión solo si hay una imagen.
        if self.imagen:
            # Abrimos la imagen en memoria con Pillow
            img = Image.open(self.imagen)
            
            # --- NUEVO: Redimensionar la imagen si es muy grande ---
            # Definimos un ancho máximo. 1200px es un buen valor para imágenes de producto.
            max_width = 1200
            if img.width > max_width:
                # Calculamos el alto proporcional para no deformar la imagen
                new_height = int((max_width / img.width) * img.height)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Creamos un buffer en memoria para la nueva imagen
            buffer = BytesIO()

            # Guardamos la imagen en el buffer en formato WebP.
            # `quality=80` es un buen balance entre calidad y tamaño. `optimize=True` ayuda un poco más.
            img.save(buffer, format='WEBP', quality=80)

            # Obtenemos el nombre del archivo original sin la extensión
            filename = os.path.splitext(os.path.basename(self.imagen.name))[0]
            new_filename = f"{filename}.webp"

            # Reemplazamos la imagen original con la nueva versión WebP en memoria.
            # `save=False` es crucial para evitar un bucle infinito de guardado.
            self.imagen.save(new_filename, ContentFile(buffer.getvalue()), save=False)

        # Finalmente, llamamos al método de guardado original.
        super().save(*args, **kwargs)

# --- SEÑAL PARA CREAR CARPETAS AUTOMÁTICAMENTE ---
@receiver(post_save, sender=Categoria)
def crear_carpeta_categoria(sender, instance, created, **kwargs):
    """
    Se ejecuta después de guardar una Categoria.
    Si la categoría es nueva (created=True), crea una carpeta para sus imágenes.
    """
    if created:
        # 1. Limpiamos el nombre de la categoría para que sea un nombre de carpeta válido.
        #    Ej: "Lijas y Abrasivos" -> "lijas-y-abrasivos"
        nombre_carpeta = slugify(instance.nombre)

        # 2. Construimos la ruta completa donde se creará la carpeta.
        #    Ej: C:\Users\Bucky\Desktop\prueba\media\productos_imagenes\lijas-y-abrasivos
        ruta_carpeta = os.path.join(settings.MEDIA_ROOT, 'productos_imagenes', nombre_carpeta)

        # 3. Creamos la carpeta. `exist_ok=True` evita errores si la carpeta ya existe.
        os.makedirs(ruta_carpeta, exist_ok=True)