import mercadopago
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Pedido, DetallePedido, Categoria 
from .carrito import Carrito
from django.db.models import Q

def home(request):
    limpieza = Producto.objects.filter(categoria__nombre__icontains="Limpieza")[:4]
    piletas = Producto.objects.filter(categoria__nombre__icontains="Piscin")[:4]
    inflables_list = Producto.objects.filter(categoria__nombre__icontains="Inflables")[:4]

    context = {
        'limpieza': limpieza,
        'piletas': piletas,
        'inflables': inflables_list,
    }
    return render(request, 'tienda/index.html', context)

def ver_categoria(request, nombre_cat):
    productos = Producto.objects.filter(categoria__nombre__icontains=nombre_cat)
    if not productos.exists():
        traductor = {'Piletas': 'Productos para piscinas', 'Inflables': 'Inflables para piscinas', 'Limpieza': 'Limpieza'}
        nombre_admin = traductor.get(nombre_cat, nombre_cat)
        productos = Producto.objects.filter(categoria__nombre__icontains=nombre_admin)
    
    query = request.GET.get('buscar')
    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
        
    return render(request, 'tienda/categoria.html', {'productos': productos, 'titulo': nombre_cat})

def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'tienda/detalle.html', {'producto': producto})

# --- GESTIÓN DEL CARRITO CON PERSISTENCIA ---

def agregar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.agregar(producto)
    
    referer = request.META.get('HTTP_REFERER', '/')
    base_url = referer.split('?')[0]
    scroll = request.GET.get('scroll', '0')
    
    url_destino = f"{base_url}?scroll={scroll}"
    if request.GET.get('show_carrito') == '1':
        url_destino += "&show_carrito=1"
        
    return redirect(url_destino)

def eliminar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.eliminar(producto)
    
    referer = request.META.get('HTTP_REFERER', '/')
    base_url = referer.split('?')[0]
    scroll = request.GET.get('scroll', '0')
    
    return redirect(f"{base_url}?scroll={scroll}&show_carrito=1")

def restar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.restar(producto)
    
    referer = request.META.get('HTTP_REFERER', '/')
    base_url = referer.split('?')[0]
    scroll = request.GET.get('scroll', '0')
    
    return redirect(f"{base_url}?scroll={scroll}&show_carrito=1")

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('home')

# --- CHECKOUT Y MERCADO PAGO ---

def checkout_carrito(request):
    carrito_instancia = Carrito(request)
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
            nombre_completo=nombre, email=email, whatsapp=whatsapp, 
            total=total_carrito, metodo_pago=metodo, estado_pago='PE'
        )
        
        items_mp = []
        for item in carrito_session.values():
            prod_obj = Producto.objects.get(id=item['producto_id'])
            DetallePedido.objects.create(
                pedido=pedido, producto=prod_obj, 
                cantidad=item['cantidad'], precio_unitario=item['precio']
            )
            items_mp.append({
                "title": item['nombre'], "quantity": int(item['cantidad']),
                "unit_price": float(item['precio']), "currency_id": "ARS",
            })

        if metodo == 'MP':
            try:
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
                    carrito_instancia.limpiar()
                    return redirect(preference["init_point"])
            except Exception as e:
                return render(request, 'tienda/checkout_carrito.html', {'total_carrito': total_carrito, 'error': str(e)})
        else:
            carrito_instancia.limpiar()
            return render(request, 'tienda/gracias_transferencia.html', {'pedido': pedido})

    return render(request, 'tienda/checkout_carrito.html', {'total_carrito': total_carrito})

def procesar_compra(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        metodo = request.POST.get('metodo_pago')
        pedido = Pedido.objects.create(nombre_completo=nombre, email=email, whatsapp=whatsapp, total=producto.precio, metodo_pago=metodo, estado_pago='PE')
        DetallePedido.objects.create(pedido=pedido, producto=producto, cantidad=1, precio_unitario=producto.precio)
        if metodo == 'MP':
            try:
                sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)
                preference_data = {"items": [{"title": str(producto.nombre), "quantity": 1, "unit_price": float(producto.precio), "currency_id": "ARS"}], "back_urls": {"success": request.build_absolute_uri('/')}, "auto_return": "approved", "binary_mode": True}
                preference_response = sdk.preference().create(preference_data)
                preference = preference_response.get("response")
                if preference and "id" in preference:
                    pedido.mp_preference_id = preference["id"]
                    pedido.save()
                    return redirect(preference["init_point"])
            except Exception as e:
                return render(request, 'tienda/checkout.html', {'producto': producto, 'error': 'Error MP'})
        else:
            return render(request, 'tienda/gracias_transferencia.html', {'pedido': pedido})
    return render(request, 'tienda/checkout.html', {'producto': producto})