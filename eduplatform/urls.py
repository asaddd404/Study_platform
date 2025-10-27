from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# 
# 👇 --- ДОБАВЬТЕ ЭТОТ ИМПОРТ --- 👇
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#
#

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
]

#
# 👇 --- ИЗМЕНИТЕ ЭТУ ЧАСТЬ --- 👇
#
# Эта строка обслуживает МЕДИА-файлы (загруженные пользователями)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Эта строка будет обслуживать СТАТИЧЕСКИЕ файлы (css, js, images)
# когда DEBUG=True
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
