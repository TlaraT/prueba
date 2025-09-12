# catalogo/models.py

from django.db import models
# --- NUEVAS IMPORTACIONES ---
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

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

    def __str__(self):
        return self.nombre

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
    
    # --- MÉTODO SAVE MODIFICADO PARA CONVERTIR IMÁGENES A WEBP ---
    def save(self, *args, **kwargs):
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

            # Creamos un buffer en memoria para la nueva imagen
            buffer = BytesIO()

            # Guardamos la imagen en el buffer en formato WebP.
            # `quality=80` es un buen balance entre calidad y tamaño.
            img.save(buffer, format='WEBP', quality=80)

            # Obtenemos el nombre del archivo original sin la extensión
            filename = os.path.splitext(os.path.basename(self.imagen.name))[0]
            new_filename = f"{filename}.webp"

            # Reemplazamos la imagen original con la nueva versión WebP en memoria.
            # `save=False` es crucial para evitar un bucle infinito de guardado.
            self.imagen.save(new_filename, ContentFile(buffer.getvalue()), save=False)

        # Finalmente, llamamos al método de guardado original.
        super().save(*args, **kwargs)