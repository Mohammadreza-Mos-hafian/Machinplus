import jdatetime

from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.core.validators import ValidationError

from cart.models import Cart, Order


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


def toman_to_rial(price):
    if price is None:
        return None

    return price * 10


def get_year():
    current_date = timezone.localdate()
    jalali_date = jdatetime.date.fromgregorian(
        date=current_date
    )

    return jalali_date.year


def validate_vendee_info(data, field_name: str):
    field = Order._meta.get_field(field_name.strip())

    try:
        field.clean(data, None)
    except ValidationError:
        raise
