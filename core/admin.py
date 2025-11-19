from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Course, Module, Lesson, Resource, 
    Test, TestQuestion, TestSubmission, TestAnswer, Progress, CourseFeature, TeacherCard
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

# Админка для Модулей
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description') # <-- 'search_fields' здесь есть
    filter_horizontal = ('teachers',)
    inlines = [LessonInline] # Показываем уроки внутри

admin.site.register(Module, ModuleAdmin)


# Админка для Уроков
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'author', 'created_at')
    list_filter = ('module__course', 'module', 'author')
    search_fields = ('title', 'content')
    autocomplete_fields = ('author', 'module') # Удобный поиск

admin.site.register(Lesson, LessonAdmin)


# Админка для Курсов
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'published', 'created_at')
    list_filter = ('published',)
    search_fields = ('title', 'description')
    filter_horizontal = ('teachers',) 
    
    class ModuleInline(admin.TabularInline):
        model = Module
        extra = 0
        fields = ('title',)
        
    inlines = [ModuleInline]
    
# admin.site.register(Course, CourseAdmin)


# ... Регистрация остальных моделей ...
admin.site.register(Resource)

# ⬇️ ⬇️ ⬇️ ВОТ ИЗМЕНЕНИЕ ⬇️ ⬇️ ⬇️
# Мы заменяем 'admin.site.register(Test)' на этот класс:

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """
    Кастомная админка для Тестов.
    """
    list_display = ('title', 'module', 'passing_score', 'created_at')
    list_filter = ('module__course',)
    
    # ЭТА СТРОКА ИСПРАВЛЯЕТ ОШИБКУ:
    search_fields = ('title', 'description') 
    
    # А эта сделает админку еще удобнее (бонус):
    autocomplete_fields = ('module',) 
    
    ordering = ('-created_at',)

# ⬆️ ⬆️ ⬆️ КОНЕЦ ИЗМЕНЕНИЯ ⬆️ ⬆️ ⬆️


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    """
    Кастомная админка для Вопросов Теста.
    """
    list_display = ('text', 'test', 'question_type', 'max_score')
    list_filter = ('test__module__course', 'test', 'question_type')
    search_fields = ('text', 'test__title')
    autocomplete_fields = ('test',) # <-- Эта строка теперь будет работать
    ordering = ('test', 'created_at')

    def get_fieldsets(self, request, obj=None):
        """
        Динамически показываем разные наборы полей 
        в зависимости от типа вопроса.
        """
        base_fields = (None, {'fields': ('test', 'text', 'question_type', 'max_score')})
        
        # Если это вопрос с выбором ответа
        if obj and obj.question_type == 'choice':
            return (
                base_fields,
                ('Варианты и Ответ (для "Выбора из вариантов")', {
                    'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')
                })
            )
        # Если это открытый вопрос
        elif obj and obj.question_type == 'open_ended':
            # Не показываем варианты и поле для ответа
            return (base_fields,)
        
        # По умолчанию (при создании нового вопроса) показываем все
        return (
            base_fields,
            ('Варианты и Ответ', {
                'description': "Для типа 'Выбор из вариантов', заполните варианты. " \
                               "После сохранения вы сможете выбрать правильный ответ из выпадающего списка.",
                'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')
            })
        )

    def get_form(self, request, obj=None, **kwargs):
        """
        Главная магия: Превращаем поле 'correct_answer' в выпадающий список.
        """
        form = super().get_form(request, obj, **kwargs)
        
        # Мы делаем это, только если РЕДАКТИРУЕМ существующий
        # вопрос типа 'choice'
        if obj and obj.question_type == 'choice':
            
            # Собираем в список только те варианты, которые не пустые
            choices = [('', '---------')] # Пустой выбор
            
            # ВАЖНО: 
            # Значением будет сам текст (obj.option_a), 
            # а отображением - "A: [текст]"
            if obj.option_a:
                choices.append((obj.option_a, f"A: {obj.option_a}"))
            if obj.option_b:
                choices.append((obj.option_b, f"B: {obj.option_b}"))
            if obj.option_c:
                choices.append((obj.option_c, f"C: {obj.option_c}"))
            if obj.option_d:
                choices.append((obj.option_d, f"D: {obj.option_d}"))
            
            # Применяем наши choices к полю 'correct_answer'
            form.base_fields['correct_answer'] = forms.ChoiceField(
                choices=choices,
                required=True, # Ставим True, т.к. у вопроса должен быть ответ
                label="Правильный ответ"
            )
        
        elif obj and obj.question_type == 'open_ended':
            # Для открытых вопросов прячем поле ответа, оно не нужно
            form.base_fields['correct_answer'].widget = forms.HiddenInput()

        return form


admin.site.register(TestSubmission)
admin.site.register(TestAnswer)
admin.site.register(Progress)


# # --- 1. Новая админка для "Чему вы научитесь" ---
# @admin.register(CourseFeature)
# class CourseFeatureAdmin(admin.ModelAdmin):
#     list_display = ('title', 'course', 'order') # Показываем важное в списке
#     list_filter = ('course',) # Позволяем фильтровать по курсу
#     search_fields = ('title', 'description')
#     autocomplete_fields = ('course',) # Удобный поиск курса
#     ordering = ('order',)
#     fields = ('course', 'order', 'title', 'description', 'icon_svg')

# # --- 2. Новая админка для "Карточек преподавателей" ---
# @admin.register(TeacherCard)
# class TeacherCardAdmin(admin.ModelAdmin):
#     list_display = ('name', 'course', 'order') # Показываем важное в списке
#     list_filter = ('course',) # Позволяем фильтровать по курсу
#     search_fields = ('name', 'description')
#     autocomplete_fields = ('course',) # Удобный поиск курса
#     ordering = ('order',)
#     fields = ('course', 'order', 'name', 'description', 'photo')