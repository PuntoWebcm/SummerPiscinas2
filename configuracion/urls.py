from django.contrib import admin
from django.urls import path, include  # <-- Agregamos 'include'
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tienda.urls')),
] 

# Sacamos el IF para que funcione siempre, incluso en el servidor real
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)