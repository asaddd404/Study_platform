from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm # <-- 1. ИМПОРТИРУЕМ НАШУ ФОРМУ

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    
    # 2. ИСПРАВЛЯЕМ ССЫЛКУ НА ВХОД:
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        authentication_form=CustomAuthenticationForm # <-- 3. ИСПОЛЬЗУЕМ НАШУ ФОРМУ
    ), name='login'),
    
    path('logout/', views.custom_logout, name='logout'),
    path('course/', views.course, name='course'),
    path('lessons/<uuid:lesson_id>/', views.lesson, name='lesson'),
    path('lessons/<uuid:lesson_id>/description/', views.lesson_description, name='lesson_description'),
    path('lessons/<uuid:lesson_id>/resources/', views.lesson_resources, name='lesson_resources'),
    path('tests/<uuid:module_id>/', views.test_module, name='test_module'),
    path('profile/', views.profile, name='profile'),
    path('api/lessons/', views.lesson_list_api, name='lesson_list_api'),
]