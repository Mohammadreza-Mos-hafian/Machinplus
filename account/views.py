from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from account.forms import RegisterForm


# Create your views here.
class UserLogoutView(LoginRequiredMixin, LogoutView):
    def get_success_url(self):
        return reverse_lazy('core:home')


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegisterForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('account:login')
    success_message = 'حساب کاربری با موفقیت ایجاد شد، لطفا وارد شوید.'


class UserLoginView(LoginView):
    template_name = 'account/login.html'
