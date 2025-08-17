from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from books.models import Book

RESERVATION_DAYS = 7
RES_LIMIT = getattr(settings, 'RESERVATION_LIMIT_PER_USER', 3)

class ReservationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status='ACTIVE')
    
    def not_expired(self):
        return self.filter(due_date__gte=timezone.now())
    
    def for_user(self, user):
        return self.filter(user=user)
    
    def expired(self):
        return self.filter(status='EXPIRED')

    def overdue_active(self):
        return self.filter(status='ACTIVE', due_date__lt=timezone.now())

    def expire_overdue(self):
        return self.overdue_active().update(status='EXPIRED')


class Reservation(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('CANCELED', 'Canceled'),
        ('EXPIRED', 'Expired'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)  # 예약 만료일(픽업 기한 등)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    canceled_at = models.DateTimeField(null=True, blank=True)

    objects = ReservationQuerySet.as_manager()

    def refresh_and_mark_expired(self, save=True):
        """
        상세 조회 시 즉시 만료 반영 헬퍼.
        - ACTIVE 상태인데 due_date가 지났으면 EXPIRED로 바꿔줌
        - save=True면 DB에도 반영
        """
        if self.status == 'ACTIVE' and self.due_date and self.due_date <= timezone.now():
            self.status = 'EXPIRED'
            if save:
                super().save(update_fields=['status'])


    class Meta:
        indexes = [
            models.Index(fields=['due_date', 'user', 'book', 'status']),
        ]
        # Postgres 사용 시엔 아래 주석 해제해서 'ACTIVE'에 한해 유니크 강제 가능
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['user', 'book'],
        #         condition=models.Q(status='ACTIVE'),
        #         name='uniq_active_reservation_per_user_book',
        #     )
        # ]

    def save(self, *args, **kwargs):
        # 1) 대출가능 도서 예약 금지
        if getattr(self.book, 'book_status', None) != '대출중':
            raise ValidationError('대출중인 도서만 예약할 수 있습니다.')

        # 2) 활성 예약 중복 방지 (만료된 건 제외)
        if not self.pk and Reservation.objects.active().not_expired().filter(
            user=self.user, book=self.book
        ).exists():
            raise ValidationError('이미 활성 예약이 존재합니다.')
        
        if not self.pk:
            active_cnt = Reservation.objects.active().not_expired().for_user(self.user).count()
            if active_cnt >= RES_LIMIT:
                raise ValidationError(f'예약은 동시에 최대 {RES_LIMIT}권까지 가능합니다. (현재 {active_cnt}권 보유)')
        
        # 3) 신규 생성 시 만료일 자동 설정
        if not self.pk and not self.due_date:
            self.due_date = timezone.now() + timedelta(days=RESERVATION_DAYS)

        # 4) 저장 직전 만료 상태 반영
        if self.status == 'ACTIVE' and self.due_date and self.due_date < timezone.now():
            self.status = 'EXPIRED'

        super().save(*args, **kwargs)

    def cancel(self) -> bool:
        """
        ACTIVE → CANCELED 로 전환.
        이미 CANCELED/EXPIRED 면 False 반환(변경 없음).
        """
        if self.status != 'ACTIVE':
            return False
        self.status = 'CANCELED'
        self.canceled_at = timezone.now()
        self.save(update_fields=['status', 'canceled_at'])
        return True

    def __str__(self):
        return f"{self.user} → {self.book} ({self.status})"


