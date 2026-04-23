from django.contrib import admin
from django.urls import path, include  # <-- Agregamos 'include'
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # <--- AGREGÁ ESTA LÍNEA
from django.urls import re_path # <--- AGREGÁ ESTA LÍNEA

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tienda.urls')),
    
    # Esta línea es la que fuerza a Django a servir las fotos en Render
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]