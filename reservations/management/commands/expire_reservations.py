# reservations/management/commands/expire_reservations.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from reservations.models import Reservation

class Command(BaseCommand):
    help = '기한이 지난 ACTIVE 예약을 EXPIRED로 일괄 전환합니다.'

    def handle(self, *args, **options):
        updated = Reservation.objects.expire_overdue()
        self.stdout.write(self.style.SUCCESS(
            f'[{timezone.now():%Y-%m-%d %H:%M:%S}] 만료 처리: {updated}건'
        ))
