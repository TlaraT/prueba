from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from collections import defaultdict
from django.templatetags.static import static as static_url
from django.conf import settings # <-- IMPORTAMOS SETTINGS

def inicio(request):
    # --- VISTA OPTIMIZADA ---
    # 1. Obtenemos todos los productos "más vendidos" en una sola consulta.
    productos_destacados = Producto.objects.filter(es_mas_vendido=True).select_related('categoria').order_by('categoria__nombre')

    # 2. Los agrupamos por categoría en Python (mucho más rápido que hacer múltiples consultas).
    productos_por_categoria = defaultdict(list)
    for producto in productos_destacados:
        # Nos aseguramos de no mostrar más de 5 productos por categoría
        if len(productos_por_categoria[producto.categoria]) < 5:
            productos_por_categoria[producto.categoria].append(producto)

    # 3. Creamos la lista final en el formato que la plantilla espera.
    datos_por_categoria = []
    for categoria, productos in productos_por_categoria.items():
        datos_por_categoria.append({
            'categoria': categoria,
            'productos': productos
        })

    # --- NUEVO: Novedades (últimos 8 productos añadidos) ---
    productos_novedades = Producto.objects.order_by('-id')[:settings.PRODUCTOS_NOVEDADES_INICIO]

    # --- NUEVO: Productos en Stock (últimos 8 productos con stock) ---
    productos_en_stock_inicio = Producto.objects.filter(stock__gt=0).order_by('-id')[:settings.PRODUCTOS_EN_STOCK_INICIO]

    context = {'datos_por_categoria': datos_por_categoria, 'productos_novedades': productos_novedades, 'productos_en_stock_inicio': productos_en_stock_inicio}
    return render(request, 'inicio.html', context)

def catalogo(request):
    # Obtenemos el término de búsqueda de la URL, si existe
    query = request.GET.get('q')
    
    if query:
        # --- LÓGICA DE BÚSQUEDA ---
        # Si hay un 'query', buscamos en todos los productos
        productos_list = Producto.objects.filter(nombre__icontains=query).order_by('nombre')
        
        paginator = Paginator(productos_list, settings.PRODUCTOS_POR_PAGINA) 
        page_number = request.GET.get('page')
        productos_pagina = paginator.get_page(page_number)

        context = {
            'is_search_results': True,
            'productos': productos_pagina,
            'query': query,
        }
        return render(request, 'catalogo.html', context)
    
    else:
        # --- LÓGICA DE CATEGORÍAS (si no hay búsqueda) ---
        # --- LÓGICA CORREGIDA Y SIMPLIFICADA PARA BUSCAR IMÁGENES DE PORTADA ---
        
        # 1. Obtenemos solo las categorías principales (las que no tienen padre).
        categorias_principales = Categoria.objects.filter(parent__isnull=True).order_by('nombre')
        #    Usamos prefetch_related para cargar todas las subcategorías de una vez y evitar
        #    múltiples consultas a la base de datos dentro del bucle.
        categorias_principales = categorias_principales.prefetch_related('subcategorias')

        # 2. Construimos la lista de datos para la plantilla.
        datos_categorias = []
        for categoria in categorias_principales:
            # --- LÓGICA DE BÚSQUEDA DE IMAGEN CON PRIORIDAD ---
            
            # Prioridad 1: Buscar un producto con imagen directamente en la categoría principal.
            primer_producto_con_imagen = Producto.objects.filter(
                categoria=categoria,
                imagen__isnull=False
            ).first()
            
            # Prioridad 2: Si no se encontró, buscar en todas las subcategorías.
            if not primer_producto_con_imagen:
                # Obtenemos los IDs de todas las subcategorías de esta categoría principal.
                ids_subcategorias = [sub.id for sub in categoria.subcategorias.all()]
                if ids_subcategorias:
                    primer_producto_con_imagen = Producto.objects.filter(
                        categoria_id__in=ids_subcategorias,
                        imagen__isnull=False
                    ).first()

            datos_categorias.append({
                'categoria': categoria,
                # Pasamos el producto entero. La plantilla se encargará de acceder a la imagen.
                # --- CORRECCIÓN: Usamos el nombre 'producto_portada' que la plantilla espera ---
                'producto_portada': primer_producto_con_imagen
            })

        # Obtenemos algunos productos con stock para mostrar (los 8 más recientes)
        productos_en_stock = Producto.objects.filter(stock__gt=0).order_by('-id')[:settings.PRODUCTOS_EN_STOCK_INICIO]

        context = {
            'is_search_results': False, 
            'datos_categorias': datos_categorias,
            'productos_en_stock': productos_en_stock
        }
        return render(request, 'catalogo.html', context)

def categoria_detalle(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    # 1. Obtenemos todas las subcategorías directas de la categoría actual.
    subcategorias = categoria.subcategorias.all().order_by('nombre')

    # Obtenemos el término de búsqueda de la URL, si existe
    query = request.GET.get('q')
    
    # --- LÓGICA MEJORADA: PREPARAMOS DATOS PARA AMBOS CASOS ---
    productos_pagina = []
    datos_subcategorias = []

    if subcategorias.exists():
        # --- CASO 1: LA CATEGORÍA TIENE SUBCATEGORÍAS ---
        # Buscamos una imagen representativa para cada subcategoría.
        
        # 1. Obtenemos todos los productos con imagen que pertenecen a nuestras subcategorías.
        productos_con_imagen = Producto.objects.filter(
            categoria__in=subcategorias, 
            imagen__isnull=False
        ).order_by('categoria_id', 'id')

        # 2. Creamos un mapa para guardar solo la imagen del primer producto de cada subcategoría.
        mapa_imagenes_subcat = {}
        for producto in productos_con_imagen:
            if producto.categoria_id not in mapa_imagenes_subcat:
                mapa_imagenes_subcat[producto.categoria_id] = producto.imagen

        # 3. Construimos la lista final para la plantilla.
        for subcat in subcategorias:
            datos_subcategorias.append({
                'categoria': subcat,
                'imagen_representativa': mapa_imagenes_subcat.get(subcat.id)
            })
    else:
        # --- CASO 2: LA CATEGORÍA NO TIENE SUBCATEGORÍAS (MOSTRAMOS PRODUCTOS) ---
        productos_list = Producto.objects.filter(categoria=categoria).order_by('nombre')
        
        if query:
            productos_list = productos_list.filter(nombre__icontains=query)

        paginator = Paginator(productos_list, settings.PRODUCTOS_POR_PAGINA) 
        page_number = request.GET.get('page')
        productos_pagina = paginator.get_page(page_number)
    
    context = {
        'categoria': categoria,
        'datos_subcategorias': datos_subcategorias, # <-- Nueva estructura con imágenes
        'productos': productos_pagina,
        'query': query,
    }
    return render(request, 'categoria_detalle/categoria_detalle.html', context)

import json
from django.utils.safestring import mark_safe
from datetime import datetime

def producto_detalle(request, producto_id):
    # Usamos prefetch_related para cargar eficientemente los accesorios y los productos principales
    # en una sola consulta adicional, evitando el problema N+1.
    producto = get_object_or_404(
        Producto.objects.prefetch_related('accesorios', 'producto_principal'), 
        id=producto_id)

    # --- LÓGICA PARA DATOS ESTRUCTURADOS (JSON-LD) ---
    # Construimos el diccionario de datos aquí en Python.
    json_ld_data = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": producto.nombre,
        "description": producto.descripcion or "", # Aseguramos que no sea None
        "sku": producto.id,
        "offers": {
            "@type": "Offer",
            "url": request.build_absolute_uri(producto.get_absolute_url()),
            "priceCurrency": "MXN", # Este es un buen candidato para settings si planeas vender en otras monedas
            "price": str(producto.precio), # Convertimos a string para JSON
            "priceValidUntil": f"{datetime.now().year + 1}-12-31",
            "availability": "https://schema.org/InStock" if producto.stock > 0 else "https://schema.org/OutOfStock",
            "itemCondition": "https://schema.org/NewCondition"
        }
    }
    # Añadimos la imagen solo si existe, para evitar errores.
    if producto.imagen and hasattr(producto.imagen, 'url'):
        json_ld_data['image'] = request.build_absolute_uri(producto.imagen.url)

    context = {
        'producto': producto,
        # Convertimos el diccionario a JSON y lo marcamos como seguro para la plantilla.
        'json_ld_data': mark_safe(json.dumps(json_ld_data, ensure_ascii=False))
    }
    return render(request, 'categoria_detalle/producto_detalle.html', context)
    
def quienes_somos(request):
    return render(request, 'quienes_somos.html')

def contacto(request):
    return render(request, 'contacto.html')

# --- NUEVA VISTA PARA AUTOCOMPLETADO ---
def search_suggestions(request):
    """
    Vista que devuelve sugerencias de productos en formato JSON
    para la funcionalidad de autocompletado.
    """
    term = request.GET.get('term', '').strip()
    suggestions = []
    if len(term) >= settings.SUGERENCIAS_BUSQUEDA_MIN_CHARS: # Usamos el valor de settings
        # Obtenemos la URL de la imagen de marcador de posición una sola vez
        placeholder_url = request.build_absolute_uri(static_url('img/placeholder.png'))
        productos = Producto.objects.filter(nombre__icontains=term)[:settings.SUGERENCIAS_BUSQUEDA_MAX] # Usamos el valor de settings
        for producto in productos:
            # Obtenemos la URL de la imagen del producto o el marcador de posición
            image_url = request.build_absolute_uri(producto.imagen.url) if producto.imagen and hasattr(producto.imagen, 'url') else placeholder_url
            
            suggestions.append({
                'label': producto.nombre,
                'url': reverse('catalogo:producto_detalle', args=[producto.id]),
                'image_url': image_url # <-- AÑADIMOS LA URL DE LA IMAGEN
            })
    
    return JsonResponse(suggestions, safe=False)

def contacto(request):
    return render(request, 'contacto.html')