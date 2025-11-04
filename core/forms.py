from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Lesson, Module,Test, TestQuestion # # <-- 1. ИМПОРТИРУЕМ Lesson и Module

# ИСПРАВЛЕНИЕ:
# Класс RegisterForm был полностью удален,
# так как он не шифровал пароль и больше не используется.
#

class CustomUserCreationForm(UserCreationForm):
    """
    Кастомная форма регистрации.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        #
        # ИСПРАВЛЕНИЕ:
        # Мы наследуем поля (username, password, password2) из UserCreationForm.Meta.fields
        # и ДОБАВЛЯЕМ к ним 'email'.
        #
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #
        # Теперь 'password' и 'password2' 100% существуют в self.fields,
        # и ошибки KeyError не будет.
        #
        self.fields['username'].widget.attrs.update({'class': 'form-input'})
        self.fields['email'].widget.attrs.update({'class': 'form-input'})
        
        #
        # ИСПРАВЛЕНИЕ:
        # Поля в UserCreationForm называются 'password1' и 'password2'
        #
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})
        
        # Меняем лейблы
        self.fields['username'].label = "Логин (Имя пользователя)"
        self.fields['email'].label = "Email"
        self.fields['password1'].label = "Пароль" # <-- ИСПРАВЛЕНО
        self.fields['password2'].label = "Подтверждение пароля" # <-- ИСПРАВЛЕНО


class CustomAuthenticationForm(AuthenticationForm):
    """
    Кастомная форма входа (логина).
    """
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-input', 'autofocus': True})
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'autocomplete': 'current-password'})
    )

class ProfileForm(forms.ModelForm):
    """
    Форма профиля (добавляем CSS-классы).
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'avatar', 'bio', 'phone', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'avatar': forms.FileInput(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }
class LessonForm(forms.ModelForm):
    """
    Форма для создания и редактирования уроков учителем.
    """
    class Meta:
        model = Lesson
        # --- 2. ОБНОВЛЕННЫЙ СПИСОК ПОЛЕЙ ---
        fields = [
            'module', 'title', 'content', 
            'video_url', 'video_file', 'image_file', 'pdf_file', 
            'assignment', 'is_free_preview'
        ]
        widgets = {
            'module': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 10}),
            'video_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'video_file': forms.FileInput(attrs={'class': 'form-input'}), # <-- Новое
            'image_file': forms.FileInput(attrs={'class': 'form-input'}), # <-- Новое
            'pdf_file': forms.FileInput(attrs={'class': 'form-input'}),   # <-- Новое
            'assignment': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'is_free_preview': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            # ... (старые лейблы) ...
            'video_url': 'Ссылка на видео (Youtube/Vimeo)',
            'video_file': 'Или загрузите видео-файл',         # <-- Новое
            'image_file': 'Или загрузите изображение',     # <-- Новое
            'pdf_file': 'Или загрузите PDF-документ',         # <-- Новое
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        # Убираем 'required' у URL, так как можно загрузить файл
        self.fields['video_url'].required = False 
        
        if user and user.role == 'teacher':
            self.fields['module'].queryset = Module.objects.filter(
                teachers=user 
            ).select_related('course')
            self.fields['module'].label_from_instance = lambda obj: f"{obj.course.title} / {obj.title}"

# --- 3. НОВЫЕ ФОРМЫ ДЛЯ ТЕСТОВ ---

class TestForm(forms.ModelForm):
    """
    Форма для создания/редактирования Теста
    """
    class Meta:
        model = Test
        # --- ДОБАВЛЕНО ПОЛЕ ---
        fields = ['title', 'description', 'passing_score']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 100}),
        }
        labels = {
            'title': 'Название теста',
            'description': 'Описание (инструкция)',
            'passing_score': 'Проходной балл (в %)',
        }

class QuestionForm(forms.ModelForm):
    """
    Форма для создания/редактирования Вопроса к тесту
    """
    class Meta:
        model = TestQuestion
        # --- ДОБАВЛЕНЫ НОВЫЕ ПОЛЯ ---
        fields = [
            'text', 
            'question_type',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_answer', 
            'max_score'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            # --- НОВЫЕ ВИДЖЕТЫ ---
            'question_type': forms.Select(attrs={'class': 'form-input', 'id': 'id_question_type_select'}),
            'option_a': forms.TextInput(attrs={'class': 'form-input'}),
            'option_b': forms.TextInput(attrs={'class': 'form-input'}),
            'option_c': forms.TextInput(attrs={'class': 'form-input'}),
            'option_d': forms.TextInput(attrs={'class': 'form-input'}),
            'correct_answer': forms.TextInput(attrs={'class': 'form-input'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-input', 'value': 1}),
        }
        labels = {
            'text': 'Текст вопроса',
            'question_type': 'Тип вопроса',
            'option_a': 'Вариант А',
            'option_b': 'Вариант Б',
            'option_c': 'Вариант В',
            'option_d': 'Вариант Г',
            'correct_answer': 'Правильный ответ',
            'max_score': 'Балл за вопрос',
        }