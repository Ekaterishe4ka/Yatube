# Импортируем CreateView, чтобы создать ему наследника
from django.views.generic import CreateView
# Функция reverse_lazy позволяет получить URL по параметрам функции path()
# Берём, тоже пригодится
from django.urls import reverse_lazy
# Импортируем класс формы, чтобы сослаться на неё во view-классе
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class LoginView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('auth:login')
    template_name = 'users/login.html'


class LogoutView(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('auth:logout')
    template_name = 'users/logout.html'
