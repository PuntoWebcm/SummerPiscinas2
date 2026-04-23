from django.contrib import admin
from .models import Categoria, Producto, Pedido, DetallePedido

# Configuración de encabezados del panel
admin.site.site_header = "Panel de Summer Piscinas"
admin.site.site_title = "Summer Piscinas Admin"
admin.site.index_title = "Bienvenida al sistema de gestión"

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'stock', 'fecha_creacion']
    list_filter = ['categoria']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['precio', 'stock']

# Esto permite ver los productos comprados dentro del formulario del Pedido
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0 # No agrega filas vacías por defecto
    readonly_fields = ['producto', 'cantidad', 'precio_unitario'] # Para que no se modifique el historial

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Columnas principales en la lista de pedidos
    list_display = ['id', 'nombre_completo', 'total', 'metodo_pago', 'estado_pago', 'fecha_creacion']
    
    # Filtros laterales
    list_filter = ['estado_pago', 'metodo_pago', 'fecha_creacion']
    
    # Buscador por cliente o WhatsApp
    search_fields = ['nombre_completo', 'whatsapp', 'email']
    
    # Permite cambiar el estado (ej: de Pendiente a Pagado) desde la lista
    list_editable = ['estado_pago']
    
    # Agregamos los productos comprados al final del formulario
    inlines = [DetallePedidoInline]

    # Ordenar por los más recientes primero
    ordering = ['-fecha_creacion']