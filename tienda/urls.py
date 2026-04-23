from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    
    # --- RUTA PARA PÁGINAS DE CATEGORÍA ---
    path('categoria/<str:nombre_cat>/', views.ver_categoria, name='ver_categoria'),
    
    # --- RUTAS PARA COMPRA DIRECTA ---
    path('checkout/<int:producto_id>/', views.procesar_compra, name='checkout'),
    
    # --- RUTAS DE GESTIÓN DEL CARRITO ---
    path('agregar/<int:producto_id>/', views.agregar_producto, name="agregar"),
    path('restar/<int:producto_id>/', views.restar_producto, name="restar"),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name="eliminar"),
    path('limpiar/', views.limpiar_carrito, name="limpiar"),
    
    # --- RUTA PARA PAGAR TODO EL CARRITO ---
    path('checkout-carrito/', views.checkout_carrito, name='checkout_carrito'),
    
    # --- RETORNO DE MERCADO PAGO ---
    path('pago-confirmado/', views.home, name='pago_exitoso'),
    path('pago-fallido/', views.home, name='pago_fallido'),
    path('pago-pendiente/', views.home, name='pago_pendiente'),
]