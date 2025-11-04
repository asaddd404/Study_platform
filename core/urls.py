from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm 

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Страница профиля (теперь это "хаб")
    path('profile/', views.profile, name='profile'), 
    
    # Основной курс
    path('course/', views.course, name='course'),
    path('lessons/<uuid:lesson_id>/', views.lesson, name='lesson'),
    path('lessons/<uuid:lesson_id>/description/', views.lesson_description, name='lesson_description'),
    path('lessons/<uuid:lesson_id>/resources/', views.lesson_resources, name='lesson_resources'),
    path('tests/<uuid:module_id>/', views.test_module, name='test_module'),
    
    # API
    path('api/lessons/', views.lesson_list_api, name='lesson_list_api'),

    # <-- 1. НОВЫЕ ПУТИ ДЛЯ УЧИТЕЛЕЙ (УПРАВЛЕНИЕ УРОКАМИ) -->
    path('teacher/lessons/new/', views.teacher_lesson_create, name='teacher_lesson_create'),
    path('teacher/lessons/<uuid:lesson_id>/edit/', views.teacher_lesson_update, name='teacher_lesson_update'),
    path('teacher/lessons/<uuid:lesson_id>/delete/', views.teacher_lesson_delete, name='teacher_lesson_delete'),
    
    # <-- 2. НОВЫЕ ПУТИ ДЛЯ УЧИТЕЛЕЙ (УПРАВЛЕНИЕ УЧЕНИКАМИ) -->
    path('teacher/students/', views.teacher_student_list, name='teacher_student_list'),
    path('teacher/students/<int:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),
]