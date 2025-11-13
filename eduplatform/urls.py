from django.contrib import admin
from django.urls import path, include  # <-- Убедитесь, что 'include' импортирован
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')), # <-- 1. ДОБАВЬТЕ ЭТУ СТРОКУ
]

# 2. ЭТО ДЛЯ МЕДИА-ФАЙЛОВ (АВАТАРЫ)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 3. ЭТО ДЛЯ СТАТИКИ (CSS, JS, IMAGES) В РЕЖИМЕ РАЗРАБОТКИ
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()