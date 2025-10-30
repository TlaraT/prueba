from django.test import TestCase
from django.urls import reverse
from .models import Categoria, Producto

class CatalogoTests(TestCase):
    """
    Suite de pruebas para la aplicación 'catalogo'.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Configuración inicial que se ejecuta una sola vez para toda la clase de pruebas.
        Creamos los objetos que usaremos en múltiples tests para no repetir código.
        """
        cls.categoria = Categoria.objects.create(nombre='Pruebas')
        cls.producto = Producto.objects.create(
            nombre='Producto de Prueba',
            categoria=cls.categoria,
            precio=123.45,
            stock=10
        )

    def test_modelo_categoria_creacion(self):
        """Prueba que el modelo Categoria se crea y se representa correctamente."""
        self.assertEqual(self.categoria.nombre, 'Pruebas')
        self.assertEqual(str(self.categoria), 'Pruebas')

    def test_modelo_producto_creacion(self):
        """Prueba que el modelo Producto se crea y se asocia a una categoría."""
        self.assertEqual(self.producto.nombre, 'Producto de Prueba')
        self.assertEqual(self.producto.categoria.nombre, 'Pruebas')
        self.assertEqual(str(self.producto), 'Producto de Prueba')

    def test_vista_inicio(self):
        """Prueba que la página de inicio carga correctamente (código 200)."""
        response = self.client.get(reverse('catalogo:inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inicio.html')

    def test_vista_catalogo(self):
        """Prueba que la página de catálogo general carga correctamente (código 200)."""
        response = self.client.get(reverse('catalogo:catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalogo.html')

    def test_vista_producto_detalle(self):
        """Prueba que la página de detalle de un producto existente carga correctamente."""
        url = reverse('catalogo:producto_detalle', args=[self.producto.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Producto de Prueba') # Verifica que el nombre del producto esté en el HTML

    def test_vista_producto_no_existente(self):
        """Prueba que al intentar ver un producto que no existe, se obtiene un error 404."""
        # Usamos un ID que es muy improbable que exista, como 999
        url = reverse('catalogo:producto_detalle', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
