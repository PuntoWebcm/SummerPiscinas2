import mercadopago
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.db.models import Q
from .models import Producto, Pedido, DetallePedido, Categoria 
from .carrito import Carrito
from urllib.parse import quote

# --- CONFIGURACIÓN DE DOMINIO Y BOT ---
DOMAIN = "https://summerpiscinas.onrender.com"  # Cambialo por tu dominio real si cambia
MI_NUMERO_WHATSAPP = "543585615079"              # Tu número donde vas a recibir la notificación
API_KEY_CALLMEBOT = "2153232"                   # Tu API Key de CallMeBot

# --- HOME CON BUSCADOR ---
def home(request):
    query = request.GET.get('buscar')
    
    limpieza_qs = Producto.objects.filter(categoria__nombre__icontains="Limpieza")
    piletas_qs = Producto.objects.filter(categoria__nombre__icontains="Piscin")
    inflables_qs = Producto.objects.filter(categoria__nombre__icontains="Inflables")

    if query:
        limpieza = limpieza_qs.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
        piletas = piletas_qs.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
        inflables = inflables_qs.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
    else:
        limpieza = limpieza_qs[:4]
        piletas = piletas_qs[:4]
        inflables = inflables_qs[:4]

    context = {
        'limpieza': limpieza,
        'piletas': piletas,
        'inflables': inflables,
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

# --- GESTIÓN DEL CARRITO ---
def agregar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.agregar(producto)
    
    # Obtenemos de dónde viene el click
    referer = request.META.get('HTTP_REFERER', '/')
    
    # Limpiamos cualquier parámetro viejo que tenga el referer (como un ?buscar= o ?show_carrito= previo)
    base_url = referer.split('?')[0]
    
    # Redireccionamos a la misma página asegurando que se abra el modal del carrito
    return redirect(f"{base_url}?show_carrito=1")
def eliminar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.eliminar(producto)
    referer = request.META.get('HTTP_REFERER', '/')
    base_url = referer.split('?')[0]
    return redirect(f"{base_url}?show_carrito=1")

def restar_producto(request, producto_id):
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, id=producto_id)
    carrito.restar(producto)
    referer = request.META.get('HTTP_REFERER', '/')
    base_url = referer.split('?')[0]
    return redirect(f"{base_url}?show_carrito=1")

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('home')


# --- NUEVO FLUJO DE CHECKOUT Y PASARELA (COMO SIGMA) ---

def checkout_carrito(request):
    """ Paso 1: Recibe los datos del cliente y crea el Pedido en Base de Datos """
    carrito_session = request.session.get("carrito", {})
    if not carrito_session: 
        return redirect('home')
        
    total_carrito = sum(float(item['total']) for item in carrito_session.values())

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        localidad = request.POST.get('localidad')
        direccion = request.POST.get('direccion')
        metodo = request.POST.get('metodo_pago')

        # Creamos el registro del pedido pendiente
        pedido = Pedido.objects.create(
            nombre_completo=nombre, 
            email=email, 
            whatsapp=whatsapp, 
            localidad=localidad, 
            direccion=direccion, 
            total=total_carrito, 
            metodo_pago=metodo, 
            estado_pago='PE'  # Pendiente
        )
        
        # Guardamos los productos en el detalle
        for item in carrito_session.values():
            prod_obj = Producto.objects.get(id=item['producto_id'])
            DetallePedido.objects.create(
                pedido=pedido, 
                producto=prod_obj, 
                cantidad=item['cantidad'], 
                precio_unitario=item['precio']
            )

        request.session['pedido_id'] = pedido.id
        
        # CAMBIO CLAVE: Redireccionamos SIEMPRE a la pantalla de selección (estilo Sigma)
        return redirect('pago_seleccion')
            
    return render(request, 'tienda/checkout_carrito.html', {'total_carrito': total_carrito})


def pago_seleccion(request):
    """ Paso 2: Procesa la preferencia de Mercado Pago de forma limpia y compatible """
    pedido_id = request.session.get('pedido_id')
    if not pedido_id:
        return redirect('home')
        
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    try:
        sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

        preference_data = {
            "items": [
                {
                    "title": f"Compra en SUMMER PISCINAS - Pedido #{pedido.id}",
                    "quantity": 1,
                    "unit_price": float(pedido.total),
                    "currency_id": "ARS",
                }
            ],
            "back_urls": {
                "success": f"{DOMAIN}/pago-exitoso/",
                "failure": f"{DOMAIN}/",
                "pending": f"{DOMAIN}/pago-exitoso/"
            },
            "auto_return": "approved",
            "binary_mode": True,
        }

        preference_response = sdk.preference().create(preference_data)
        
        # COMPATIBILIDAD DE SDK: Soportar tanto formato objeto como diccionario antiguo
        if hasattr(preference_response, "get"):
            preference = preference_response.get("response", {})
        else:
            preference = getattr(preference_response, "response", {})
        
        # Extraer IDs de forma segura
        preference_id = preference.get('id', '') if preference else ''
        init_point = preference.get('init_point', '#') if preference else '#'

        if not preference_id:
            return render(request, 'tienda/checkout_carrito.html', {
                'total_carrito': pedido.total, 
                'error': f"Error de Mercado Pago: Respuesta inválida. Estructura obtenida: {preference_response}"
            })

        # Guardamos el id de preferencia de manera segura si existe en el modelo
        if hasattr(pedido, 'mp_preference_id'):
            pedido.mp_preference_id = preference_id
            pedido.save()

        return render(request, 'tienda/pago_seleccion.html', {
            'pedido': pedido,
            'preference_id': preference_id,
            'init_point': init_point
        })

    except Exception as e:
        return render(request, 'tienda/checkout_carrito.html', {
            'total_carrito': pedido.total, 
            'error': f"Excepción en el servidor: {str(e)}"
        })


def pago_exitoso(request):
    """ Paso 3: Éxito total. Descuenta stock, limpia sesión y avisa por WhatsApp al dueño """
    payment_id = request.GET.get('collection_id') or request.GET.get('payment_id') or "Transferencia"
    metodo_url = request.GET.get('metodo')
    
    pedido_id = request.session.get('pedido_id')
    
    if pedido_id:
        pedido = get_object_or_404(Pedido, id=pedido_id)
    else:
        pedido = Pedido.objects.latest('id')

    # Si viene desde Mercado Pago o se confirma transferencia, marcar pagado
    pedido.estado_pago = 'AP'  # Aprobado
    
    # Si vino por la URL de transferencia, actualizamos el método en el modelo
    if metodo_url == 'transferencia':
        pedido.metodo_pago = 'TR' # O la sigla que use tu modelo para Transferencias
    
    pedido.save()
    
    # Procesar detalles, armar texto y descontar stock
    detalles = DetallePedido.objects.filter(pedido=pedido)
    detalle_productos = ""
    
    for item in detalles:
        detalle_productos += f"- {item.cantidad}x {item.producto.nombre}\n"
        
        # Descuento de stock si tu modelo Producto maneja el campo .stock
        if hasattr(item.producto, 'stock'):
            producto = item.producto
            producto.stock = max(0, producto.stock - item.cantidad)
            producto.save()

    # --- ENVÍO DE NOTIFICACIÓN WHATSAPP VIA CALLMEBOT ---
    try:
        tipo_pago = "TRANSFERENCIA BANCARIA" if metodo_url == 'transferencia' else f"MERCADO PAGO (ID: {payment_id})"
        
        mensaje_texto = (
            f"🌊 *NUEVA VENTA SUMMER PISCINAS*\n\n"
            f"📦 *Pedido:* #{pedido.id}\n"
            f"👤 *Cliente:* {pedido.nombre_completo}\n"
            f"📱 *WhatsApp Cliente:* {pedido.whatsapp}\n"
            f"📍 *Localidad:* {pedido.localidad}\n"
            f"🏠 *Dirección:* {pedido.direccion}\n\n"
            f"🛒 *Productos:*\n{detalle_productos}\n"
            f"💰 *Total Cobrado:* ${float(pedido.total)}\n"
            f"💳 *Método:* {tipo_pago}"
        )

        mensaje_url = quote(mensaje_texto)
        url_bot = f"https://api.callmebot.com/whatsapp.php?phone={MI_NUMERO_WHATSAPP}&text={mensaje_url}&apikey={API_KEY_CALLMEBOT}"
        
        requests.get(url_bot, timeout=10)
    except Exception as e:
        print(f"Error enviando notificación: {e}")
    
    # Limpiamos el carrito de la sesión
    carrito = Carrito(request)
    carrito.limpiar()
    
    # Quitamos el ID de pedido de la sesión para dejarla lista para otra compra
    if 'pedido_id' in request.session:
        del request.session['pedido_id']
        
    return render(request, 'tienda/pago_confirmado.html', {
        'pedido': pedido, 
        'transferencia': (metodo_url == 'transferencia')
    })