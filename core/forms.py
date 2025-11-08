from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Lesson, Module, Test, TestQuestion


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
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 10}),
            'video_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'video_file': forms.FileInput(attrs={'class': 'form-input'}),
            'image_file': forms.FileInput(attrs={'class': 'form-input'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-input'}),
            'assignment': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'is_free_preview': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'video_url': 'Ссылка на видео (Youtube/Vimeo)',
            'video_file': 'Или загрузите видео-файл',
            'image_file': 'Или загрузите изображение',
            'pdf_file': 'Или загрузите PDF-документ',
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

# ... (другие формы остаются как есть) ...

class QuestionForm(forms.ModelForm):
    # Этот блок у тебя уже есть, но я его поменял
    # ⬇️ ⬇️ ⬇️
    CORRECT_CHOICES = [
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
    ]
    correct_answer = forms.ChoiceField(
        choices=CORRECT_CHOICES,
        required=False, # Необязателен для "развернутого ответа"
        widget=forms.Select(attrs={'class': 'form-input'}), # <-- Меняем виджет на Select
        label='Правильный ответ (для типа "Выбор из вариантов")'
    )
    # ⬆️ ⬆️ ⬆️

    class Meta:
        model = TestQuestion
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
        
        # ⬇️ ⬇️ ⬇️ ВОТ ЧТО НУЖНО ДОБАВИТЬ ⬇️ ⬇️ ⬇️
        # Этот блок добавит класс 'form-input' ко всем полям
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-input', 'id': 'id_question_type'}), # <-- Добавляем ID для JS
            'option_a': forms.TextInput(attrs={'class': 'form-input'}),
            'option_b': forms.TextInput(attrs={'class': 'form-input'}),
            'option_c': forms.TextInput(attrs={'class': 'form-input'}),
            'option_d': forms.TextInput(attrs={'class': 'form-input'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-input'}),
        }
        # ⬆️ ⬆️ ⬆️ ---------------------------------- ⬆️ ⬆️ ⬆️