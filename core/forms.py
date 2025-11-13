from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Lesson, Module, Test, TestQuestion
from django_summernote.widgets import SummernoteWidget  # <-- 1. ДОБАВЛЕН ЭТОТ ИМПОРТ
import re

def clean_summernote_content(html):
    if not html:
        return ''

    # 1. Убираем <br> в пустых ячейках таблицы — НО ТОЛЬКО если ячейка РЕАЛЬНО пуста
    # Было: удаляло <td><br></td> → плохо
    # Стало: оставляем <br>, если ячейка иначе была бы пустой
    html = re.sub(r'<(td|th)([^>]*)>\s*<br\s*/?>\s*</\1>', r'<\1\2><br></\1>', html)

    # 2. Убираем полностью пустые теги <p>, <div>, <h1>-<h6>
    html = re.sub(r'<(p|h[1-6]|div)([^>]*)>\s*</\1>', '', html)

    # 3. Убираем пустые <br> в конце
    html = html.strip()
    html = re.sub(r'<br\s*/?>$', '', html, flags=re.IGNORECASE)

    # 4. Убираем class="" у заголовков
    html = re.sub(r'<(h[1-6]) class="">', r'<\1>', html)

    return html.strip()

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input'})
        self.fields['email'].widget.attrs.update({'class': 'form-input'})
        
        # --- ИСПРАВЛЕНИЕ ЗДЕСЬ (было 'password') ---
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})
        
        self.fields['username'].label = "Логин (Имя пользователя)"
        self.fields['email'].label = "Email"
        
        # --- И ИСПРАВЛЕНИЕ ЗДЕСЬ (было 'password') ---
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"

class CustomAuthenticationForm(AuthenticationForm):
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
    class Meta:
        model = Lesson
        fields = [
            'module', 'title', 'content', 
            'video_url', 'video_file', 'image_file', 'pdf_file', 
            'assignment', 'is_free_preview'
        ]
        widgets = {
            'module': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            
            # ⬇️ ⬇️ ⬇️ 2. ВОТ ГЛАВНОЕ ИЗМЕНЕНИЕ ⬇️ ⬇️ ⬇️
            'content': SummernoteWidget(),
            # ⬆️ ⬆️ ⬆️ --------------------------- ⬆️ ⬆️ ⬆️
            
            'video_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'video_file': forms.FileInput(attrs={'class': 'form-input'}),
            'image_file': forms.FileInput(attrs={'class': 'form-input'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-input'}),
            'assignment': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'is_free_preview': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            # ... (ваши labels остаются без изменений) ...
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        self.fields['video_url'].required = False 
        
        if user and user.role == 'teacher':
            self.fields['module'].queryset = Module.objects.filter(
                teachers=user 
            ).select_related('course')
            self.fields['module'].label_from_instance = lambda obj: f"{obj.course.title} / {obj.title}"

# --- 3. ОБНОВЛЕННЫЕ ФОРМЫ ДЛЯ ТЕСТОВ ---

class TestForm(forms.ModelForm):
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
# eduplatform/core/forms.py
# forms.py
class QuestionForm(forms.ModelForm):
    class Meta:
        model = TestQuestion
        fields = [
            'text', 'question_type', 'option_a', 'option_b',
            'option_c', 'option_d', 'correct_answer', 'max_score'
        ]
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-input', 'id': 'id_question_type'}),
            'option_a': forms.TextInput(attrs={'class': 'form-input', 'id': 'id_option_a'}),
            'option_b': forms.TextInput(attrs={'class': 'form-input', 'id': 'id_option_b'}),
            'option_c': forms.TextInput(attrs={'class': 'form-input', 'id': 'id_option_c'}),
            'option_d': forms.TextInput(attrs={'class': 'form-input', 'id': 'id_option_d'}),
            # НЕ СКРЫВАЕМ! Оставляем как TextInput, но JS заменит
            'correct_answer': forms.TextInput(attrs={
                'class': 'form-input',
                'id': 'id_correct_answer',
                'style': 'display: none;'  # Скрываем визуально
            }),
            'max_score': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'value': 1}),
        }
        labels = {
            'text': 'Текст вопроса',
            'question_type': 'Тип вопроса',
            'option_a': 'Вариант А',
            'option_b': 'Вариант Б',
            'option_c': 'Вариант В',
            'option_d': 'Вариант Г',
            'correct_answer': 'Правильный ответ',
            'max_score': 'Макс. балл за вопрос'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['correct_answer'].required = False