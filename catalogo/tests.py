from django.test import TestCase

from .models import Producto  # Asegúrate de importar tu modelo Producto

class ProductoModelTest(TestCase):

    def test_producto_se_crea_correctamente(self):
        """
        Prueba que un objeto Producto puede ser creado en la base de datos
        y su nombre se guarda correctamente.
        """
        # 1. Preparación: Crea un nuevo producto
        producto = Producto.objects.create(nombre="Martillo de Uña", precio=150.00, stock=25)

        # 2. Afirmación (Assertion): Comprueba si el resultado es el esperado
        #    Buscamos el producto que acabamos de guardar.
        producto_guardado = Producto.objects.get(id=producto.id)
        
        #    Usamos 'self.assertEqual' para verificar si el nombre del producto guardado
        #    es exactamente "Martillo de Uña".
        self.assertEqual(producto_guardado.nombre, "Martillo de Uña")
# Create your tests here.
