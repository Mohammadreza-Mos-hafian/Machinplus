from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView

from account.forms import RegisterForm
from cart.services import merge_guest_cart_to_user


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

    def form_valid(self, form):
        # ذخیره شناسه سشن مهمان قبل از ورود
        guest_session_key = self.request.session.session_key

        response = super().form_valid(form)
        
        # ادغام سبد خرید مهمان با سبد کاربر
        merge_guest_cart_to_user(
            user=self.request.user,
            guest_session_key=guest_session_key,
        )

        return response
