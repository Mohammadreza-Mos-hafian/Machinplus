import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction, IntegrityError
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from shop.models import Product
from .services import get_cart_for_request, release_order_stock
from .models import Cart, CartItem, Order, OrderItem
from utils.functions import get_safe_redirect_url, get_user_cart


def get_cart_summary(cart):
    """
    محاسبه خلاصه سبد خرید در سمت سرور.

    items_count: تعداد محصولات متمایز
    total_quantity: مجموع تعداد تمام محصولات
    subtotal: جمع قیمت محصولات دارای قیمت مشخص
    has_unpriced_items: وجود محصول نیازمند استعلام قیمت
    """
    items = list(
        cart.items.select_related('product').all()
    )

    subtotal = Decimal('0')
    total_quantity = 0
    has_unpriced_items = False

    for item in items:
        total_quantity += item.quantity

        product = item.product

        if product is None:
            item.can_be_priced = False
            item.is_price_on_request = True
            has_unpriced_items = True
            continue

        item.is_price_on_request = (
                product.price_on_request or product.price is None
        )

        item.can_be_priced = not item.is_price_on_request

        if item.is_price_on_request:
            has_unpriced_items = True
        else:
            subtotal += product.price * item.quantity

    return {
        'items': items,
        'items_count': len(items),
        'total_quantity': total_quantity,
        'subtotal': subtotal,
        'has_unpriced_items': has_unpriced_items,
    }


@transaction.atomic
def get_owned_order(request, order_id):
    """
    دریافت سفارش و بررسی مالکیت آن.

    اگر سفارش متعلق به مهمان باشد و توکن Session معتبر باشد،
    در صورت ورود کاربر، سفارش به حساب او منتقل می‌شود.
    """

    order = (
        Order.objects
        .select_for_update()
        .filter(pk=order_id)
        .first()
    )

    if not order:
        return None

    session_token = request.session.get('checkout_token')

    # کاربر واردشده
    if request.user.is_authenticated:

        # سفارش از قبل متعلق به همین کاربر است.
        if order.user_id == request.user.pk:
            return order

        # سفارش متعلق به مهمان است؛ توکن باید مطابقت داشته باشد.
        if (
                order.user_id is None
                and session_token
                and str(order.checkout_token) == str(session_token)
        ):
            order.user = request.user
            order.save(update_fields=['user'])
            return order

        return None

    # مهمان
    if (
            order.user_id is None
            and session_token
            and str(order.checkout_token) == str(session_token)
    ):
        return order

    return None



class CartDetailView(TemplateView):
    template_name = 'cart.html'

    def dispatch(self, request, *args, **kwargs):
        order_id = request.session.get('pending_order_id')

        if order_id:
            order = get_owned_order(request, order_id)

            if not order:
                request.session.pop('pending_order_id', None)

                messages.warning(
                    request,
                    'امکان دسترسی به سفارش قبلی وجود ندارد.'
                )

            elif order.status == 'pending':

                # فقط سفارش دارای زمان انقضای گذشته، منقضی است.
                if (
                    order.expires_at
                    and order.expires_at <= timezone.now()
                ):
                    order = release_order_stock(order.pk)

                    request.session.pop('pending_order_id', None)

                    if order.status == 'paid':
                        messages.info(
                            request,
                            'این سفارش قبلاً پرداخت شده است.'
                        )

                    elif order.status == 'cancelled':
                        # اگر توکن Session متعلق به همین سفارش است،
                        # برای Checkout بعدی توکن جدید ایجاد می‌کنیم.
                        if (
                            str(request.session.get('checkout_token'))
                            == str(order.checkout_token)
                        ):
                            request.session['checkout_token'] = str(
                                uuid.uuid4()
                            )

                        messages.warning(
                            request,
                            'مهلت پرداخت سفارش قبلی به پایان رسیده است. '
                            'می‌توانید سفارش جدیدی ثبت کنید.'
                        )

                    else:
                        messages.warning(
                            request,
                            'وضعیت سفارش قبلی قابل تأیید نیست. '
                            'لطفاً با پشتیبانی تماس بگیرید.'
                        )

                elif order.stock_reserved:
                    return redirect('cart:payment')

                else:
                    request.session.pop('pending_order_id', None)

                    messages.warning(
                        request,
                        'وضعیت رزرو موجودی سفارش معتبر نیست. '
                        'لطفاً سفارش خود را مجدداً ثبت کنید.'
                    )

            else:
                request.session.pop('pending_order_id', None)

                if order.status == 'paid':
                    messages.info(
                        request,
                        'سفارش قبلی شما پرداخت شده است.'
                    )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart = get_user_cart(self.request)

        context['cart'] = cart

        if not cart:
            context.update({
                'items': [],
                'cart_items_count': 0,
                'total_quantity': 0,
                'subtotal': Decimal('0'),
                'has_unpriced_items': False,
            })
            return context

        summary = get_cart_summary(cart)

        context.update(summary)
        context['cart_items_count'] = summary['items_count']

        return context


class CheckoutView(TemplateView):
    template_name = 'checkout.html'

    FORM_FIELDS = (
        'first_name',
        'last_name',
        'phone',
        'email',
        'postal_code',
        'recipient',
        'address',
        'delivery_description',
    )

    def get_initial_form_data(self):
        user = self.request.user

        data = {
            'first_name': '',
            'last_name': '',
            'phone': '',
            'email': '',
            'postal_code': '',
            'recipient': '',
            'address': '',
            'delivery_description': '',
        }

        if user.is_authenticated:
            data.update({
                'first_name': (user.first_name or '').strip(),
                'last_name': (user.last_name or '').strip(),
                'email': (user.email or '').strip(),
            })

        return data

    def dispatch(self, request, *args, **kwargs):
        self.cart = get_cart_for_request(request)

        if not self.cart or not self.cart.items.exists():
            messages.warning(
                request,
                'سبد خرید شما خالی است.'
            )
            return redirect('cart:cart_detail')

        self.form_data = self.get_initial_form_data()

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not request.session.get('checkout_token'):
            request.session['checkout_token'] = str(uuid.uuid4())

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items = list(
            self.cart.items.select_related('product').all()
        )

        subtotal = Decimal('0')
        total_quantity = 0
        has_price_on_request = False

        for item in items:
            product = item.product
            total_quantity += item.quantity

            if product is None:
                item.is_price_on_request = True
                item.line_total = None
                has_price_on_request = True
                continue

            if (
                    getattr(product, 'price_on_request', False)
                    or product.price is None
            ):
                item.is_price_on_request = True
                item.line_total = None
                has_price_on_request = True
            else:
                item.is_price_on_request = False
                item.line_total = product.price * item.quantity
                subtotal += item.line_total

        items_count = len(items)

        context.update({
            'cart': self.cart,
            'items': items,
            'items_count': items_count,
            'cart_items_count': items_count,
            'total_quantity': total_quantity,
            'subtotal': subtotal,
            'total': subtotal,
            'has_price_on_request': has_price_on_request,
            'can_proceed_to_payment': not has_price_on_request,
            'checkout_token': self.request.session.get('checkout_token'),
            'form_data': self.form_data,
        })

        return context

    def post(self, request, *args, **kwargs):
        self.form_data = {
            field: request.POST.get(field, '').strip()
            for field in self.FORM_FIELDS
        }

        # اعتبارسنجی فیلدهای ضروری
        required_fields = {
            'نام': 'first_name',
            'نام خانوادگی': 'last_name',
            'شماره تماس': 'phone',
            'کد پستی': 'postal_code',
            'آدرس': 'address',
        }

        for label, field in required_fields.items():
            if not self.form_data[field]:
                messages.error(
                    request,
                    f'وارد کردن {label} الزامی است.'
                )
                return self.render_to_response(
                    self.get_context_data()
                )

        # اعتبارسنجی ایمیل
        if self.form_data['email']:
            try:
                validate_email(self.form_data['email'])
            except ValidationError:
                messages.error(
                    request,
                    'آدرس ایمیل معتبر نیست.'
                )
                return self.render_to_response(
                    self.get_context_data()
                )

        # اعتبارسنجی توکن
        token = request.POST.get('checkout_token', '')

        if (
                not token
                or token != request.session.get('checkout_token')
        ):
            messages.error(
                request,
                'درخواست تسویه‌حساب معتبر نیست. صفحه را مجدداً بارگذاری کنید.'
            )
            return redirect('cart:checkout')

        # بررسی سفارش قبلی با همین توکن
        existing_order = Order.objects.filter(
            checkout_token=token
        ).first()

        if existing_order:
            owned_order = get_owned_order(
                request,
                existing_order.pk
            )

            if not owned_order:
                messages.error(
                    request,
                    'امکان دسترسی به این سفارش وجود ندارد.'
                )
                return redirect('cart:cart_detail')

            # سفارش هنوز قابل پرداخت است
            if owned_order.status in ('pending', 'paid'):
                request.session['pending_order_id'] = owned_order.pk
                return redirect('cart:payment')

            # سفارش قبلی لغو شده یا دیگر قابل پرداخت نیست.
            # توکن جدید می‌سازیم و با همین اطلاعات فرم،
            # سفارش جدید را ایجاد می‌کنیم.
            request.session.pop('pending_order_id', None)

            token = str(uuid.uuid4())
            request.session['checkout_token'] = token

        try:
            order = self.create_order(
                token=token,
                **self.form_data,
            )

        except ValidationError as error:
            messages.error(
                request,
                error.messages[0] if error.messages else str(error)
            )
            return self.render_to_response(
                self.get_context_data()
            )

        except IntegrityError:
            # ممکن است درخواست هم‌زمان دیگری با همین توکن
            # سفارش ایجاد کرده باشد.
            existing_order = (
                Order.objects
                .filter(checkout_token=token)
                .first()
            )

            if existing_order:
                owned_order = get_owned_order(
                    request,
                    existing_order.pk
                )

                if (
                        owned_order
                        and owned_order.status in ('pending', 'paid')
                ):
                    request.session['pending_order_id'] = owned_order.pk
                    return redirect('cart:payment')

            raise

        request.session['pending_order_id'] = order.pk

        messages.success(
            request,
            'سفارش شما با موفقیت ثبت شد.'
        )

        return redirect('cart:payment')

    @transaction.atomic
    def create_order(
            self,
            *,
            token,
            first_name,
            last_name,
            phone,
            email,
            postal_code,
            recipient,
            address,
            delivery_description,
    ):
        # قفل اقلام سبد خرید
        cart_items = list(
            CartItem.objects.select_for_update()
            .filter(cart=self.cart)
            .select_related('product')
        )

        if not cart_items:
            raise ValidationError(
                'سبد خرید شما خالی است.'
            )

        product_ids = [
            item.product_id
            for item in cart_items
            if item.product_id is not None
        ]

        # قفل محصولات
        products = (
            Product.objects
            .select_for_update()
            .filter(pk__in=product_ids)
            .order_by('pk')
        )

        products_by_id = {
            product.pk: product
            for product in products
        }

        subtotal = Decimal('0')
        validated_items = []

        # بررسی محصولات و محاسبه قیمت
        for item in cart_items:
            product = products_by_id.get(item.product_id)

            if product is None:
                raise ValidationError(
                    'یکی از محصولات سبد خرید دیگر موجود نیست.'
                )

            product_name = getattr(
                product,
                'title',
                str(product)
            )

            if not product.is_active:
                raise ValidationError(
                    f'محصول «{product_name}» غیرفعال شده است.'
                )

            if not product.is_available:
                raise ValidationError(
                    f'محصول «{product_name}» در حال حاضر موجود نیست.'
                )

            if (
                    getattr(product, 'price_on_request', False)
                    or product.price is None
            ):
                raise ValidationError(
                    f'محصول «{product_name}» نیازمند استعلام قیمت است.'
                )

            if item.quantity > product.stock:
                raise ValidationError(
                    f'موجودی محصول «{product_name}» کافی نیست. '
                    f'موجودی فعلی: {product.stock}'
                )

            line_total = product.price * item.quantity
            subtotal += line_total

            validated_items.append({
                'product': product,
                'quantity': item.quantity,
                'unit_price': product.price,
                'total_price': line_total,
            })

        shipping_cost = Decimal('0')
        total = subtotal + shipping_cost

        # ایجاد سفارش
        order = Order.objects.create(
            checkout_token=token,
            user=(
                self.request.user
                if self.request.user.is_authenticated
                else None
            ),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            postal_code=postal_code,
            recipient=recipient,
            address=address,
            delivery_description=delivery_description,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            status='pending',
            stock_reserved=True,
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        # ایجاد اقلام سفارش و رزرو موجودی
        for item_data in validated_items:
            product = item_data['product']
            quantity = item_data['quantity']

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=getattr(
                    product,
                    'title',
                    str(product)
                ),
                product_sku=getattr(
                    product,
                    'sku',
                    ''
                ) or '',
                quantity=quantity,
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price'],
            )

            product.stock -= quantity

            product.save(
                update_fields=['stock']
            )

        # سبد خرید پس از پرداخت موفق پاک‌سازی خواهد شد.

        return order


class PaymentView(TemplateView):
    template_name = 'payment.html'

    def dispatch(self, request, *args, **kwargs):
        # دریافت شناسه سفارش از Session
        order_id = request.session.get('pending_order_id')

        if not order_id:
            messages.warning(
                request,
                'سفارشی برای پرداخت پیدا نشد.'
            )
            return redirect('cart:cart_detail')

        # دریافت سفارش و بررسی مالکیت
        self.order = get_owned_order(
            request,
            order_id
        )

        if not self.order:
            request.session.pop('pending_order_id', None)

            messages.error(
                request,
                'شما اجازه دسترسی به این سفارش را ندارید.'
            )
            return redirect('cart:cart_detail')

        # بررسی پرداخت قبلی
        if self.order.status == 'paid':
            request.session.pop('pending_order_id', None)

            messages.info(
                request,
                'این سفارش قبلاً پرداخت شده است.'
            )
            return redirect('cart:cart_detail')

        # بررسی وضعیت سفارش
        if self.order.status != 'pending':
            request.session.pop('pending_order_id', None)

            messages.warning(
                request,
                'این سفارش در وضعیت قابل پرداخت قرار ندارد.'
            )
            return redirect('cart:cart_detail')

        # بررسی انقضای سفارش
        if (
                self.order.expires_at
                and self.order.expires_at <= timezone.now()
        ):
            released_order = release_order_stock(
                self.order.pk
            )

            request.session.pop('pending_order_id', None)

            if released_order.status == 'paid':
                messages.info(
                    request,
                    'این سفارش قبلاً پرداخت شده است.'
                )
                return redirect('cart:cart_detail')

            # اگر سفارش واقعاً لغو شده باشد، توکن قبلی را
            # کنار می‌گذاریم تا Checkout سفارش قبلی را پیدا نکند.
            if released_order.status == 'cancelled':
                request.session['checkout_token'] = str(uuid.uuid4())

                messages.warning(
                    request,
                    'مهلت پرداخت این سفارش به پایان رسیده است. '
                    'لطفاً سفارش جدیدی ثبت کنید.'
                )
                return redirect('cart:checkout')

            # اگر آزادسازی به هر دلیل سفارش را لغو نکرده باشد،
            # اجازه ادامه پرداخت نمی‌دهیم.
            messages.warning(
                request,
                'وضعیت سفارش تغییر کرده است. لطفاً دوباره بررسی کنید.'
            )
            return redirect('cart:cart_detail')

        # بررسی رزرو موجودی
        if not self.order.stock_reserved:
            request.session.pop('pending_order_id', None)

            messages.error(
                request,
                'موجودی سفارش رزرو نشده است. '
                'امکان ادامه پرداخت وجود ندارد.'
            )
            return redirect('cart:cart_detail')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order_items = self.order.items.all()

        cart = get_cart_for_request(self.request)
        cart_items_count = cart.items.count() if cart else 0

        context.update({
            'order': self.order,
            'order_items': order_items,
            'subtotal': self.order.subtotal,
            'shipping_cost': self.order.shipping_cost,
            'total': self.order.total,
            'items_count': order_items.count(),
            'total_quantity': sum(
                item.quantity for item in order_items
            ),
            'payment_available': False,
            'cart_items_count': cart_items_count,
        })

        return context

    def post(self, request, *args, **kwargs):
        messages.info(
            request,
            'درگاه پرداخت هنوز فعال نشده است.'
        )

        return redirect('cart:payment')


class PaymentResultView(TemplateView):
    template_name = 'payment_result.html'


@require_POST
@transaction.atomic
def add_to_cart(request):
    product_id = request.POST.get("product_id")

    if not product_id:
        messages.error(
            request,
            "محصول موردنظر مشخص نشده است."
        )
        return get_safe_redirect_url(request)

    try:
        product = (
            Product.objects
            .select_for_update()
            .get(pk=product_id)
        )
    except (Product.DoesNotExist, ValueError, TypeError):
        messages.error(
            request,
            "محصول موردنظر پیدا نشد."
        )
        return get_safe_redirect_url(request)

    if not product.is_active:
        messages.error(
            request,
            "این محصول در حال حاضر فعال نیست."
        )
        return get_safe_redirect_url(request)

    if product.price_on_request or product.price is None:
        messages.warning(
            request,
            "این محصول نیازمند استعلام قیمت است و امکان افزودن آن به سبد خرید وجود ندارد."
        )
        return get_safe_redirect_url(request)

    if not product.is_available or product.stock <= 0:
        messages.warning(
            request,
            "این محصول در حال حاضر موجود نیست."
        )
        return get_safe_redirect_url(request)

    cart = get_cart_for_request(request)

    if not cart:
        messages.error(
            request,
            "امکان دسترسی به سبد خرید وجود ندارد."
        )
        return get_safe_redirect_url(request)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": 1},
    )

    if created:
        messages.success(
            request,
            f"محصول «{product.title}» به سبد خرید اضافه شد."
        )
    else:
        messages.info(
            request,
            "این محصول قبلاً در سبد خرید شما وجود دارد."
        )

    return get_safe_redirect_url(request)


@require_POST
@transaction.atomic
def delete_item(request):
    """
    حذف یک محصول از سبد خرید.
    """
    cart = get_user_cart(request)

    if not cart:
        return redirect('cart:cart_detail')

    item = get_object_or_404(
        CartItem.objects.select_for_update(),
        pk=request.POST.get('cart_item_id'),
        cart=cart,
    )

    item.delete()

    messages.success(request, 'محصول از سبد خرید حذف شد.')

    # عمداً خود Cart را حذف نمی‌کنیم.
    return redirect('cart:cart_detail')


@require_POST
@transaction.atomic
def update_item_quantity(request, item_id):
    """
    افزایش یا کاهش تعداد یک محصول در سبد خرید.
    """
    cart = get_user_cart(request)

    if not cart:
        return JsonResponse({
            'success': False,
            'message': 'سبد خرید شما پیدا نشد.',
        }, status=404)

    item = get_object_or_404(
        CartItem.objects.select_for_update(),
        pk=item_id,
        cart=cart,
    )

    if item.product_id is None:
        return JsonResponse({
            'success': False,
            'message': 'این محصول دیگر در دسترس نیست.',
        }, status=400)

    product = get_object_or_404(
        Product.objects.select_for_update(),
        pk=item.product_id,
    )

    action = request.POST.get('action')

    if not product.is_active or not product.is_available:
        return JsonResponse({
            'success': False,
            'message': 'این محصول در حال حاضر قابل خرید نیست.',
        }, status=400)

    if action == 'increase':

        if item.quantity >= product.stock:
            return JsonResponse({
                'success': False,
                'message': 'موجودی محصول کافی نیست.',
            }, status=400)

        item.quantity += 1

    elif action == 'decrease':

        if item.quantity <= 1:
            return JsonResponse({
                'success': False,
                'message': 'حداقل تعداد سفارش یک عدد است.',
            }, status=400)

        item.quantity -= 1

    else:
        return JsonResponse({
            'success': False,
            'message': 'درخواست نامعتبر است.',
        }, status=400)

    item.save(update_fields=['quantity'])

    summary = get_cart_summary(cart)

    return JsonResponse({
        'success': True,
        'quantity': item.quantity,
        'stock': product.stock,
        'subtotal': str(summary['subtotal']),
        'items_count': summary['items_count'],
        'total_quantity': summary['total_quantity'],
        'has_unpriced_items': summary['has_unpriced_items'],
    })
