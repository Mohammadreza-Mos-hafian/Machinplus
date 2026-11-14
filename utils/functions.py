from django.contrib.auth.base_user import AbstractBaseUser
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from cart.models import Cart


def get_safe_redirect_url(request):
    next_url = request.META.get('HTTP_REFERER')

    if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect('/')


def get_user_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(
            user=request.user
        ).first()
    elif request.session.session_key:
        cart = Cart.objects.filter(
            session_key=request.session.session_key
        ).first()
    else:
        cart = None

    return cart
