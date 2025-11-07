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
    path('profile/', views.profile, name='profile'), 
    
    # --- СТРАНИЦА КУРСА (ОСНОВНОЙ "ХАБ") ---
    path('course/', views.course, name='course'),
    
    # --- СТАРЫЕ ССЫЛКИ (для прямых заходов) ---
    path('lesson/<uuid:lesson_id>/', views.lesson, name='lesson'),
    path('tests/<uuid:module_id>/', views.test_module, name='test_module'),
    
    # --- 1. НОВЫЕ ПУТИ ДЛЯ HTMX (ЧАСТИЧНЫЕ) ---
    path('partials/lesson/<uuid:lesson_id>/', views.partial_lesson_detail, name='partial_lesson_detail'),
    path('partials/test/<uuid:module_id>/', views.partial_test_module, name='partial_test_module'),
    # -------------------------------------------
    
    path('lessons/<uuid:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    
    # ... (старые API, lesson_description, lesson_resources - не трогаем) ...
    path('lessons/<uuid:lesson_id>/description/', views.lesson_description, name='lesson_description'),
    path('lessons/<uuid:lesson_id>/resources/', views.lesson_resources, name='lesson_resources'),
    path('api/lessons/', views.lesson_list_api, name='lesson_list_api'),

    # --- УПРАВЛЕНИЕ УЧИТЕЛЕМ (без изменений) ---
    path('teacher/lessons/new/', views.teacher_lesson_create, name='teacher_lesson_create'),
    path('teacher/lessons/<uuid:lesson_id>/edit/', views.teacher_lesson_update, name='teacher_lesson_update'),
    path('teacher/lessons/<uuid:lesson_id>/delete/', views.teacher_lesson_delete, name='teacher_lesson_delete'),
    
    path('teacher/module/<uuid:module_id>/test/create/', views.teacher_test_create, name='teacher_test_create'),
    path('teacher/test/<uuid:test_id>/edit/', views.teacher_test_update, name='teacher_test_update'),
    path('teacher/test/<uuid:test_id>/delete/', views.teacher_test_delete, name='teacher_test_delete'),
    
    path('teacher/question/<uuid:question_id>/edit/', views.teacher_question_update, name='teacher_question_update'),
    path('teacher/question/<uuid:question_id>/delete/', views.teacher_question_delete, name='teacher_question_delete'),
    
    path('teacher/students/', views.teacher_student_list, name='teacher_student_list'),
    path('teacher/students/<int:student_id>/', views.teacher_student_detail, name='teacher_student_detail'),
    path('teacher/student/<int:student_id>/remove/', views.teacher_remove_student, name='teacher_remove_student'),
]