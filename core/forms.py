from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Lesson, Module # <-- 1. ИМПОРТИРУЕМ Lesson и Module
#
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
        # Убираем 'author' из полей, он будет назначаться автоматически
        fields = ['module', 'title', 'content', 'video_url', 'assignment', 'is_free_preview']
        widgets = {
            'module': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 10}),
            'video_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'assignment': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'is_free_preview': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'module': 'Модуль',
            'title': 'Название занятия',
            'content': 'Содержание (текст урока)',
            'video_url': 'Ссылка на видео (необязательно)',
            'assignment': 'Задание к уроку (необязательно)',
            'is_free_preview': 'Бесплатный предпросмотр (доступен без прохождения предыдущих)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        if user and user.role == 'teacher':
            #
            # <-- ИЗМЕНЕННАЯ ЛОГИКА -->
            #
            # Показываем только те модули, 
            # в которых этот учитель числится в 'teachers'
            self.fields['module'].queryset = Module.objects.filter(
                teachers=user # <-- ВОТ ИЗМЕНЕНИЕ
            ).select_related('course')
            
            # (Опционально) Делаем название модуля понятнее
            self.fields['module'].label_from_instance = lambda obj: f"{obj.course.title} / {obj.title}"