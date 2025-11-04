from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Course, Module, Lesson, Resource, 
    Test, TestQuestion, TestSubmission, TestAnswer, Progress
)

# Переопределяем админку Пользователя, чтобы было видно роль
class CustomUserAdmin(UserAdmin):
    model = User
    # Добавляем 'role' в список полей
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('role', 'avatar', 'bio', 'phone', 'is_teacher_approved')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

admin.site.register(User, CustomUserAdmin)


# --- Настройка управления Курсами, Модулями и Уроками ---

# Позволяет добавлять Уроки прямо на странице Модуля (опционально, но удобно)
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1 # Показать 1 пустой слот для нового урока
    fields = ('title', 'author', 'created_at')
    readonly_fields = ('created_at',)
    # Мы не можем автоматически задать 'author' здесь, 
    # так как у inline нет доступа к 'request'.
    # Автор будет назначаться, если урок создан из профиля учителя.
    # Уроки, созданные в админке, нужно будет назначить вручную.

# Админка для Модулей
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description')
    
    # <-- ВОТ ГЛАВНАЯ ЧАСТЬ -->
    # Удобный интерфейс "двойного списка" для выбора учителей
    filter_horizontal = ('teachers',)
    
    inlines = [LessonInline] # Показываем уроки внутри

# Регистрируем Модуль с новыми настройками
admin.site.register(Module, ModuleAdmin)


# Админка для Уроков
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'author', 'created_at')
    list_filter = ('module__course', 'module', 'author')
    search_fields = ('title', 'content')
    # Позволяем менять автора в админке
    autocomplete_fields = ('author', 'module') # Удобный поиск

admin.site.register(Lesson, LessonAdmin)


# Админка для Курсов
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'published', 'created_at')
    list_filter = ('published',)
    search_fields = ('title', 'description')
    # Тоже добавляем удобный выбор учителей на уровне курса
    filter_horizontal = ('teachers',)
    
    # Показываем модули внутри курса
    class ModuleInline(admin.TabularInline):
        model = Module
        extra = 0
        fields = ('title',)
        
    inlines = [ModuleInline]

admin.site.register(Course, CourseAdmin)


# ... Регистрация остальных моделей ...
admin.site.register(Resource)
admin.site.register(Test)
admin.site.register(TestQuestion)
admin.site.register(TestSubmission)
admin.site.register(TestAnswer)
admin.site.register(Progress)