from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria
from django.core.paginator import Paginator
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

    context = {'datos_por_categoria': datos_por_categoria}
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
        categorias = Categoria.objects.all().order_by('nombre')
        datos_categorias = []
        for categoria in categorias:
            primer_producto = Producto.objects.filter(categoria=categoria, imagen__isnull=False).first()
            datos_categorias.append({
                'categoria': categoria,
                'primer_producto': primer_producto
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

def producto_detalle(request, producto_id):
    # Usamos prefetch_related para cargar eficientemente los accesorios y los productos principales
    # en una sola consulta adicional, evitando el problema N+1.
    producto = get_object_or_404(
        Producto.objects.prefetch_related('accesorios', 'producto_principal'), 
        id=producto_id)
    context = {
        'producto': producto
    }
    return render(request, 'categoria_detalle/producto_detalle.html', context)
    
def quienes_somos(request):
    return render(request, 'quienes_somos.html')

def contacto(request):
    return render(request, 'contacto.html')