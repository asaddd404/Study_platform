from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
]

# Эта строка для МЕДИА (загруженные аватары)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 👇 ЭТОТ БЛОК НУЖЕН ДЛЯ CSS/JS
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()