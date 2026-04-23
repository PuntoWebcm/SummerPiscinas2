from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, verbose_name="Categoría")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del producto")
    descripcion = models.TextField(verbose_name="Descripción")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    stock = models.PositiveIntegerField(verbose_name="Stock disponible")
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True, verbose_name="Imagen")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de carga")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

class Pedido(models.Model):
    METODOS_PAGO = [
        ('MP', 'Mercado Pago / Tarjetas'),
        ('TR', 'Transferencia Bancaria'),
    ]
    
    ESTADOS_PAGO = [
        ('PE', 'Pendiente'),
        ('PA', 'Pagado'),
        ('RE', 'Rechazado'),
    ]

    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    email = models.EmailField(verbose_name="Correo Electrónico")
    whatsapp = models.CharField(max_length=20, verbose_name="WhatsApp")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total")
    metodo_pago = models.CharField(max_length=2, choices=METODOS_PAGO, verbose_name="Medio de Pago")
    estado_pago = models.CharField(max_length=2, choices=ESTADOS_PAGO, default='PE', verbose_name="Estado")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Pedido")
    
    mp_preference_id = models.CharField(max_length=250, blank=True, null=True, verbose_name="ID Preferencia MP")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"Pedido {self.id} - {self.nombre_completo}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre if self.producto else 'Producto eliminado'}"