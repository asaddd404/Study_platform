from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

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
        self.fields['password'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})
        
        # Меняем лейблы
        self.fields['username'].label = "Логин (Имя пользователя)"
        self.fields['email'].label = "Email"
        self.fields['password'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"


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