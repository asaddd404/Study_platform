from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Course, Module, Lesson, Resource, 
    Test, TestQuestion, TestSubmission, TestAnswer, Progress
)

# Переопределяем админку Пользователя
class CustomUserAdmin(UserAdmin):
    model = User
    # Добавляем 'role' в список полей
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('role', 'avatar', 'bio', 'phone', 'is_teacher_approved')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

admin.site.register(User, CustomUserAdmin)


# --- НОВЫЙ БЛОК ДЛЯ УПРАВЛЕНИЯ КУРСАМИ ---

# Позволяет добавлять Уроки прямо на странице Модуля
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1 # Показать 1 пустой слот для нового урока
    fields = ('title', 'author', 'created_at')
    readonly_fields = ('author', 'created_at') # Автор будет ставиться автоматически

# Админка для Модулей
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description')
    
    # <-- ВОТ ГЛАВНАЯ ЧАСТЬ -->
    # Удобный интерфейс "двойного списка" для выбора учителей
    filter_horizontal = ('teachers',)
    
    inlines = [LessonInline] # Показываем уроки внутри

admin.site.register(Module, ModuleAdmin)


# Админка для Уроков
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'author', 'created_at')
    list_filter = ('module__course', 'module', 'author')
    search_fields = ('title', 'content')
    # Делаем автора "только для чтения", т.к. он назначается при создании
    readonly_fields = ('author',) 

admin.site.register(Lesson, LessonAdmin)


# Админка для Курсов
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'published', 'created_at')
    list_filter = ('published',)
    search_fields = ('title', 'description')
    # Тоже добавляем удобный выбор
    filter_horizontal = ('teachers',)

admin.site.register(Course, CourseAdmin)


# ... (Регистрация остальных моделей, если нужно) ...
admin.site.register(Resource)
admin.site.register(Test)
admin.site.register(TestQuestion)
admin.site.register(TestSubmission)
admin.site.register(TestAnswer)
admin.site.register(Progress)