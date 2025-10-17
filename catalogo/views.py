from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from collections import defaultdict

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
    productos_novedades = Producto.objects.order_by('-id')[:8]

    # --- NUEVO: Productos en Stock (últimos 8 productos con stock) ---
    productos_en_stock_inicio = Producto.objects.filter(stock__gt=0).order_by('-id')[:8]

    context = {'datos_por_categoria': datos_por_categoria, 'productos_novedades': productos_novedades, 'productos_en_stock_inicio': productos_en_stock_inicio}
    return render(request, 'inicio.html', context)

def catalogo(request):
    # Obtenemos el término de búsqueda de la URL, si existe
    query = request.GET.get('q')
    
    if query:
        # --- LÓGICA DE BÚSQUEDA ---
        # Si hay un 'query', buscamos en todos los productos
        productos_list = Producto.objects.filter(nombre__icontains=query).order_by('nombre')
        
        paginator = Paginator(productos_list, 12) 
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
        # --- LÓGICA DE CATEGORÍAS OPTIMIZADA para evitar el problema N+1 ---
        categorias = Categoria.objects.all().order_by('nombre')
        
        # 1. Obtenemos todos los productos con imagen, ordenados por categoría, en una sola consulta.
        productos_con_imagen = Producto.objects.filter(
            categoria__in=categorias, 
            imagen__isnull=False
        ).order_by('categoria_id', 'id')

        # 2. Creamos un mapa para guardar solo el primer producto de cada categoría (sin más consultas).
        mapa_primer_producto = {}
        for producto in productos_con_imagen:
            if producto.categoria_id not in mapa_primer_producto:
                mapa_primer_producto[producto.categoria_id] = producto

        # 3. Construimos la lista final usando el mapa, de forma súper rápida.
        datos_categorias = []
        for categoria in categorias:
            datos_categorias.append({
                'categoria': categoria,
                'primer_producto': mapa_primer_producto.get(categoria.id)
            })

        # Obtenemos algunos productos con stock para mostrar (los 8 más recientes)
        productos_en_stock = Producto.objects.filter(stock__gt=0).order_by('-id')[:8]

        context = {
            'is_search_results': False, 
            'datos_categorias': datos_categorias,
            'productos_en_stock': productos_en_stock
        }
        return render(request, 'catalogo.html', context)

def categoria_detalle(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    # Obtenemos el término de búsqueda de la URL, si existe
    query = request.GET.get('q')
    
    # Empezamos con todos los productos de la categoría
    productos_list = Producto.objects.filter(categoria=categoria).order_by('nombre')
    
    # Si hay un término de búsqueda, filtramos la lista
    if query:
        productos_list = productos_list.filter(nombre__icontains=query)

    paginator = Paginator(productos_list, 12) 
    page_number = request.GET.get('page')
    productos_pagina = paginator.get_page(page_number)

    context = {
        'categoria': categoria,
        'productos': productos_pagina,
        'query': query, # Enviamos la búsqueda de vuelta a la plantilla
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
            "priceCurrency": "MXN",
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
    if len(term) >= 2: # Empezar a buscar a partir de 2 caracteres
        productos = Producto.objects.filter(nombre__icontains=term)[:10] # Limitar a 10 resultados
        for producto in productos:
            suggestions.append({
                'label': producto.nombre,
                'url': reverse('catalogo:producto_detalle', args=[producto.id])
            })
    
    return JsonResponse(suggestions, safe=False)

def contacto(request):
    return render(request, 'contacto.html')