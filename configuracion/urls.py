from django.contrib import admin
from django.urls import path, include  # <-- Agregamos 'include'
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tienda.urls')),  # <-- Esto conecta las rutas de tu app
] 

# Esto es para que Django pueda servir las fotos de las piletas en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)