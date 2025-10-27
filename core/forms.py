from django import forms
from django.contrib.auth.forms import UserCreationForm # Импортируем базовую форму
from .models import User # Импортируем нашу модель

# 
# ВОТ НОВАЯ ФОРМА
#
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User # Указываем, что наша модель - это core.User
        fields = ('username', 'email') # Указываем поля для регистрации (можете добавить 'first_name', 'last_name' и т.д.)

#
# Ваша существующая форма остается ниже
#
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'avatar', 'bio', 'phone', 'first_name', 'last_name']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
