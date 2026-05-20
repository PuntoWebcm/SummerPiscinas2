from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    
    # --- RUTA PARA PÁGINAS DE CATEGORÍA ---
    path('categoria/<str:nombre_cat>/', views.ver_categoria, name='ver_categoria'),
    
    # --- RUTAS DE GESTIÓN DEL CARRITO ---
    path('agregar/<int:producto_id>/', views.agregar_producto, name="agregar"),
    path('restar/<int:producto_id>/', views.restar_producto, name="restar"),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name="eliminar"),
    path('limpiar/', views.limpiar_carrito, name="limpiar"),
    
    # --- FLUJO DE CHECKOUT UNIFICADO (ESTILO SIGMA) ---
    # Paso 1: Formulario de datos del cliente
    path('checkout-carrito/', views.checkout_carrito, name='checkout_carrito'),
    
    # Paso 2: Elección de pasarela / Botón de Mercado Pago
    path('pago-seleccion/', views.pago_seleccion, name='pago_seleccion'),
    
    # Paso 3: Retorno exitoso (Procesa stock, limpia sesión y te manda el WhatsApp)
    path('pago-exitoso/', views.pago_exitoso, name='pago_exitoso'),
    
    # --- RUTAS AUXILIARES ---
    path('pago-fallido/', views.home, name='pago_fallido'),
    path('pago-pendiente/', views.home, name='pago_pendiente'),
]