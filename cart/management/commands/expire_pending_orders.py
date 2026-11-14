from django.core.management.base import BaseCommand
from django.utils import timezone

from cart.models import Order
from cart.services import release_order_stock


class Command(BaseCommand):
    help = 'Expire pending orders and release reserved stock.'

    def handle(self, *args, **options):
        now = timezone.now()

        order_ids = list(
            Order.objects.filter(
                status='pending',
                stock_reserved=True,
                stock_released_at__isnull=True,
                expires_at__isnull=False,
                expires_at__lte=now,
            )
            .order_by('expires_at')
            .values_list('pk', flat=True)[:500]
        )

        expired_count = 0

        for order_id in order_ids:
            order = release_order_stock(order_id)

            if (
                order.status == 'cancelled'
                and order.stock_released_at is not None
            ):
                expired_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{expired_count} expired order(s) processed.'
            )
        )
