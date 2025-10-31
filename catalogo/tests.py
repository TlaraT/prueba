from django.test import TestCase
from django.urls import reverse
from .models import Categoria, Producto
from django.db.utils import IntegrityError

class CategoriaModelTests(TestCase):
    """
    Pruebas específicas para el modelo Categoria y su lógica de jerarquía.
    """
    def test_modelo_categoria_creacion(self):
        """Prueba que el modelo Categoria se crea y se representa correctamente."""
        cat = Categoria.objects.create(nombre='Herramientas')
        self.assertEqual(cat.nombre, 'Herramientas')
        self.assertEqual(str(cat), 'Herramientas')

    def test_modelo_subcategoria_creacion(self):
        """Prueba que una subcategoría se crea y se asocia a su padre correctamente."""
        parent = Categoria.objects.create(nombre='Herramientas')
        child = Categoria.objects.create(nombre='Eléctricas', parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertEqual(str(child), 'Herramientas > Eléctricas')

    def test_unique_toplevel_category_name(self):
        """Prueba que no se pueden crear dos categorías principales con el mismo nombre."""
        Categoria.objects.create(nombre='Plomería')
        with self.assertRaises(IntegrityError):
            Categoria.objects.create(nombre='Plomería')

    def test_unique_subcategory_name_within_parent(self):
        """Prueba que no se puede crear una subcategoría con el mismo nombre bajo el mismo padre."""
        parent = Categoria.objects.create(nombre='Herramientas')
        Categoria.objects.create(nombre='Manuales', parent=parent)
        with self.assertRaises(IntegrityError):
            Categoria.objects.create(nombre='Manuales', parent=parent)

    def test_allowed_duplicate_subcategory_name_across_parents(self):
        """Prueba que SÍ se puede crear una subcategoría con el mismo nombre bajo DIFERENTES padres."""
        parent1 = Categoria.objects.create(nombre='Herramientas')
        parent2 = Categoria.objects.create(nombre='Jardinería')
        
        # Esto debe funcionar sin errores
        sub1 = Categoria.objects.create(nombre='Doméstico', parent=parent1)
        sub2 = Categoria.objects.create(nombre='Doméstico', parent=parent2)
        
        self.assertEqual(sub1.nombre, 'Doméstico')
        self.assertEqual(sub2.nombre, 'Doméstico')
        self.assertNotEqual(sub1.id, sub2.id)
        self.assertEqual(Categoria.objects.filter(nombre='Doméstico').count(), 2)


class CatalogoViewsTests(TestCase):
    """
    Pruebas para las vistas de la aplicación 'catalogo'.
    """
    @classmethod
    def setUpTestData(cls):
        """Configuración inicial con una estructura de categorías y productos."""
        # Categorías principales
        cls.cat_herramientas = Categoria.objects.create(nombre='Herramientas')
        cls.cat_plomeria = Categoria.objects.create(nombre='Plomería')
        cls.cat_vacia = Categoria.objects.create(nombre='Categoría Vacía')

        # Subcategorías
        cls.sub_electricas = Categoria.objects.create(nombre='Eléctricas', parent=cls.cat_herramientas)
        cls.sub_manuales = Categoria.objects.create(nombre='Manuales', parent=cls.cat_herramientas)

        # Productos
        cls.prod_taladro = Producto.objects.create(nombre='Taladro', categoria=cls.sub_electricas, precio=100)
        cls.prod_martillo = Producto.objects.create(nombre='Martillo', categoria=cls.sub_manuales, precio=20)
        cls.prod_tubo = Producto.objects.create(nombre='Tubo PVC', categoria=cls.cat_plomeria, precio=10)
        # Producto en la categoría principal para probar la lógica de imágenes
        cls.prod_destornillador = Producto.objects.create(nombre='Destornillador', categoria=cls.cat_herramientas, precio=5)

    def test_modelo_producto_creacion(self):
        """Prueba que el modelo Producto se crea y se asocia a una categoría."""
        self.assertEqual(self.prod_taladro.nombre, 'Taladro')
        self.assertEqual(self.prod_taladro.categoria, self.sub_electricas)
        self.assertEqual(str(self.prod_taladro), 'Taladro')

    def test_vista_inicio(self):
        """Prueba que la página de inicio carga correctamente (código 200)."""
        response = self.client.get(reverse('catalogo:inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inicio.html')
    
    def test_vista_catalogo_muestra_solo_categorias_principales(self):
        """Prueba que la vista de catálogo solo lista categorías sin padre."""
        response = self.client.get(reverse('catalogo:catalogo'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalogo.html')
        
        # Verificamos que las categorías principales están en el contexto
        categorias_en_contexto = [item['categoria'] for item in response.context['datos_categorias']]
        self.assertIn(self.cat_herramientas, categorias_en_contexto)
        self.assertIn(self.cat_plomeria, categorias_en_contexto)
        self.assertIn(self.cat_vacia, categorias_en_contexto)

        # Verificamos que las subcategorías NO están en el contexto
        self.assertNotIn(self.sub_electricas, categorias_en_contexto)
        self.assertNotIn(self.sub_manuales, categorias_en_contexto)

    def test_vista_catalogo_logica_imagen_portada(self):
        """Prueba que la vista de catálogo asigna la imagen de portada correctamente."""
        # Nota: Esta prueba asume que los productos tienen imágenes.
        # Para una prueba real, deberíamos crear archivos de imagen falsos.
        # Aquí, solo verificamos que se asigna un producto de portada.
        response = self.client.get(reverse('catalogo:catalogo'))
        datos = response.context['datos_categorias']

        # Para 'Herramientas', debe encontrar 'Destornillador' (producto en la cat. principal)
        dato_herramientas = next(item for item in datos if item['categoria'] == self.cat_herramientas)
        self.assertEqual(dato_herramientas['producto_portada'], self.prod_destornillador)

        # Para 'Plomería', debe encontrar 'Tubo PVC'
        dato_plomeria = next(item for item in datos if item['categoria'] == self.cat_plomeria)
        self.assertEqual(dato_plomeria['producto_portada'], self.prod_tubo)

        # Para 'Categoría Vacía', no debe haber producto de portada
        dato_vacia = next(item for item in datos if item['categoria'] == self.cat_vacia)
        self.assertIsNone(dato_vacia['producto_portada'])

    def test_vista_categoria_detalle_con_subcategorias(self):
        """Prueba que la página de detalle de una categoría con hijos muestra las subcategorías."""
        url = reverse('catalogo:categoria_detalle', args=[self.cat_herramientas.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categoria_detalle/categoria_detalle.html')

        # Verifica que se pasen las subcategorías y no los productos
        self.assertIn('datos_subcategorias', response.context)
        self.assertTrue(response.context['datos_subcategorias']) # Debe tener contenido
        self.assertFalse(response.context['productos']) # Debe estar vacío

        # Verifica que el HTML contenga los nombres de las subcategorías
        self.assertContains(response, self.sub_electricas.nombre)
        self.assertContains(response, self.sub_manuales.nombre)
        # Verifica que NO contenga nombres de productos directamente
        self.assertNotContains(response, self.prod_taladro.nombre)

    def test_vista_categoria_detalle_sin_subcategorias(self):
        """Prueba que la página de detalle de una categoría sin hijos muestra los productos."""
        url = reverse('catalogo:categoria_detalle', args=[self.sub_electricas.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categoria_detalle/categoria_detalle.html')

        # Verifica que se pasen los productos y no las subcategorías
        self.assertIn('productos', response.context)
        self.assertTrue(response.context['productos']) # Debe tener contenido
        self.assertFalse(response.context['datos_subcategorias']) # Debe estar vacío

        # Verifica que el HTML contenga el nombre del producto
        self.assertContains(response, self.prod_taladro.nombre)

    def test_vista_producto_detalle(self):
        """Prueba que la página de detalle de un producto existente carga correctamente."""
        url = reverse('catalogo:producto_detalle', args=[self.prod_taladro.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Taladro') # Verifica que el nombre del producto esté en el HTML

    def test_vista_producto_no_existente(self):
        """Prueba que al intentar ver un producto que no existe, se obtiene un error 404."""
        url = reverse('catalogo:producto_detalle', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
