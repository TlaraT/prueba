# catalogo/models.py

from django.db import models
    

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
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    imagen = models.ImageField(upload_to='productos_imagenes/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    es_mas_vendido = models.BooleanField(default=False)
    

    def __str__(self):
        return self.nombre
    
    