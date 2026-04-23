import mercadopago
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Pedido, DetallePedido
from .carrito import Carrito

def home(request):
    # Usamos los nombres EXACTOS de tu panel de admin
    # "Limpieza" -> OK
    limpieza = Producto.objects.filter(categoria__nombre__icontains="Limpieza")[:4]
    
    # Cambiamos "Piletas" por "Piscinas" para que coincida con "Productos para piscinas"
    piletas = Producto.objects.filter(categoria__nombre__icontains="Piscinas")[:4]
    
    # "Equipamiento" -> Coincide con "Equipamiento para piscinas"
    equipamiento = Producto.objects.filter(categoria__nombre__icontains="Equipamiento")[:4]

    context = {
        'limpieza': limpieza,
        'piletas': piletas,
        'equipamiento': equipamiento,
    }
    return render(request, 'tienda/index.html', context)

def ver_categoria(request, nombre_cat):
    # Esta vista es para la página independiente de cada sección
    productos = Producto.objects.filter(categoria__nombre__icontains=nombre_cat)
    
    # Si alguien busca dentro de la categoría
    busqueda = request.GET.get('buscar')
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    return render(request, 'tienda/categoria.html', {
        'productos': productos,
        'titulo': nombre_cat
    })

def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'tienda/detalle.html', {'producto': producto})

# --- GESTIÓN DEL CARRITO ---

def agregar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.agregar(producto)
    
    # Manejo de redirección dinámica para no cerrar el modal
    if request.GET.get('next') == 'carrito':
        return redirect(request.META.get('HTTP_REFERER', 'home') + '?show_carrito=1')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def eliminar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.eliminar(producto)
    
    if request.GET.get('next') == 'carrito':
        return redirect(request.META.get('HTTP_REFERER', 'home') + '?show_carrito=1')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def restar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.restar(producto)
    
    if request.GET.get('next') == 'carrito':
        return redirect(request.META.get('HTTP_REFERER', 'home') + '?show_carrito=1')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# --- CHECKOUT PARA CARRITO COMPLETO (CON FORMULARIO) ---

def checkout_carrito(request):
    carrito_session = request.session.get("carrito", {})
    if not carrito_session:
        return redirect('home')

    total_carrito = sum(float(item['total']) for item in carrito_session.values())

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        metodo = request.POST.get('metodo_pago')

        pedido = Pedido.objects.create(
            nombre_completo=nombre,
            email=email,
            whatsapp=whatsapp,
            total=total_carrito,
            metodo_pago=metodo,
            estado_pago='PE'
        )
        
        items_mp = []
        for item in carrito_session.values():
            prod_obj = Producto.objects.get(id=item['producto_id'])
            DetallePedido.objects.create(
                pedido=pedido,
                producto=prod_obj,
                cantidad=item['cantidad'],
                precio_unitario=item['precio']
            )
            items_mp.append({
                "title": item['nombre'],
                "quantity": int(item['cantidad']),
                "unit_price": float(item['precio']),
                "currency_id": "ARS",
            })

        if metodo == 'MP':
            sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            preference_data = {
                "items": items_mp,
                "back_urls": {
                    "success": request.build_absolute_uri('/'),
                    "failure": request.build_absolute_uri('/'),
                    "pending": request.build_absolute_uri('/'),
                },
                "auto_return": "approved",
                "binary_mode": True,
            }

            preference_response = sdk.preference().create(preference_data)
            preference = preference_response.get("response")

            if preference and "id" in preference:
                pedido.mp_preference_id = preference["id"]
                pedido.save()
                request.session['carrito'] = {}
                return redirect(preference["init_point"])
            else:
                return render(request, 'tienda/checkout_carrito.html', {
                    'total_carrito': total_carrito,
                    'error': 'Error de comunicación con Mercado Pago.'
                })
        else:
            request.session['carrito'] = {}
            return render(request, 'tienda/gracias_transferencia.html', {'pedido': pedido})

    return render(request, 'tienda/checkout_carrito.html', {'total_carrito': total_carrito})

def procesar_compra(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        metodo = request.POST.get('metodo_pago')
        
        pedido = Pedido.objects.create(
            nombre_completo=nombre,
            email=email,
            whatsapp=whatsapp,
            total=producto.precio,
            metodo_pago=metodo,
            estado_pago='PE'
        )
        
        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=1,
            precio_unitario=producto.precio
        )
        
        if metodo == 'MP':
            sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
            preference_data = {
                "items": [{"title": str(producto.nombre), "quantity": 1, "unit_price": float(producto.precio), "currency_id": "ARS"}],
                "back_urls": {"success": request.build_absolute_uri('/'), "failure": request.build_absolute_uri('/'), "pending": request.build_absolute_uri('/')},
                "auto_return": "approved",
                "binary_mode": True,
            }
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response.get("response")
            
            if preference and "id" in preference:
                pedido.mp_preference_id = preference["id"]
                pedido.save()
                return redirect(preference["init_point"])
            else:
                return render(request, 'tienda/checkout.html', {'producto': producto, 'error': 'Error con Mercado Pago'})
        else:
            return render(request, 'tienda/gracias_transferencia.html', {'pedido': pedido})
            
    return render(request, 'tienda/checkout.html', {'producto': producto})