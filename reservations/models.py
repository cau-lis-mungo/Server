from django.conf import settings
# from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Exists, OuterRef
from django.db.models.functions import Now, TruncDate
from django.utils import timezone
from books.models import Book, BookStatus

def _limit() -> int:
    return getattr(settings, "RESERVATION_LIMIT_PER_USER", 3)

def _reservation_days() -> int:
    return getattr(settings, "RESERVATION_DAYS", 7)

class ReservationStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "예약중"
    CANCELED = "CANCELED", "예약취소"
    EXPIRED = "EXPIRED", "예약만료"

class ReservationQuerySet(models.QuerySet):
    # 유효한 예약
    def active(self):
        return self.filter(status=ReservationStatus.ACTIVE)
        
    # 반납된 도서에 대한 유효한 예약
    def not_expired(self):
        return self.active().filter(due_date__gte=TruncDate(Now()))
    
    # 사용자별 예약
    def for_user(self, user):
        return self.filter(user=user)
    
    # 만료된 예약
    def expired(self):
        return self.filter(status=ReservationStatus.EXPIRED)
    
    # 반납된 도서에 대한 기간이 초과된 예약 (만료 처리 예정)
    def overdue_active(self):
        # 만료일을 지나면 자동 만료 대상으로
        return self.active().filter(due_date__lt=TruncDate(Now()))
    
    # 만료 처리
    def expire_overdue(self):
        return self.overdue_active().update(status=ReservationStatus.EXPIRED)
    
    def expire_overdue_and_release_books(self):
        updated = self.expire_overdue()

        has_active = self.active().filter(book=OuterRef("pk"))
        qs = Book.objects.filter(book_status=BookStatus.RESERVED).annotate(has_active=Exists(has_active)).filter(has_active=False)
        fixed = 0
        for b in qs:
            if b.book_status != BookStatus.AVAILABLE:
                b.book_status = BookStatus.AVAILABLE
                b.save(update_fields=["book_status"])
            fixed += 1
        return updated, fixed

class Reservation(models.Model):
    # STATUS_CHOICES = (
    #     ('ACTIVE', '예약중'),
    #     ('CANCELED', '예약취소'),
    #     ('EXPIRED', '예약만료'),
    # )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    reservation_date = models.DateTimeField(auto_now_add=True) # 예약일
    due_date = models.DateField(null=True, blank=True) # 예약만료일
    cancel_date = models.DateTimeField(null=True, blank=True) # 예약취소일

    status = models.CharField(
        max_length=10,
        choices=ReservationStatus.choices,
        default=ReservationStatus.ACTIVE,
    )

    objects = ReservationQuerySet.as_manager()

    class Meta:
        ordering = ['-reservation_date'] # 최근 예약 순
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=Q(status=ReservationStatus.ACTIVE),
                name="uq_active_reservation_per_user_book",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.book} ({self.status})"

    # def clean(self):
    #     # 대출가능 도서에는 예약 불가
    #     if getattr(self.book, "status", None) == "대출가능":
    #         raise ValidationError("해당 도서는 예약할 수 없습니다.")

    def clean(self):
        # if Reservation.objects.filter(user=self.user, book=self.book, status="ACTIVE").exclude(pk=self.pk).exists():
        #     raise ValidationError({"message": "이미 이 도서를 예약하셨습니다."})

        allowed_statuses = {BookStatus.RENTED, BookStatus.RESERVED}
        book_status = getattr(self.book, "book_status", None)

        if book_status not in allowed_statuses:
            raise ValidationError("이 도서는 예약할 수 없습니다.")
        
        # 예약 개수 제한
        active_count = Reservation.objects.active().for_user(self.user).count()
        if self.pk:
            active_count = Reservation.objects.active().for_user(self.user).exclude(pk=self.pk).count()
        if active_count >= _limit():
            raise ValidationError(f"예약 가능 권수는 최대 {_limit()}권입니다.")
    
    # 취소
    def cancel(self):
        if self.status != ReservationStatus.ACTIVE:
            raise ValidationError({'message': ['이미 취소되었거나 만료된 예약입니다.']})
        self.status = ReservationStatus.CANCELED
        self.cancel_date = timezone.now()
        self.save(update_fields=["status", "cancel_date"])

        book = self.book

        # 대출 여부 확인
        try:
            from rentals.models import Rental
            is_rented = Rental.objects.filter(book=book, returned_at__isnull=True).exists()
        except Exception:
            is_rented = False

        # 남은 활성 예약 존재 여부
        has_active_resv = Reservation.objects.active().filter(book=book).exists()

        # 최종 상태 결정
        new_status = (
            BookStatus.RENTED if is_rented
            else BookStatus.RESERVED if has_active_resv
            else BookStatus.AVAILABLE
        )

        if book.book_status != new_status:
            book.book_status = new_status
            book.save(update_fields=["book_status"])
    
    # 다음 예약자에게 예약만기일 부여
    def next_resv(self, days: int | None = None):
        days = days or _reservation_days()
        self.due_date = timezone.localdate() + timezone.timedelta(day=days)
        self.save(update_fields=["due_date"])
    
    # 만료
    # def mark_expired(self):
    #     if self.status != "ACTIVE":
    #         return
    #     self.status = "EXPIRED"
    #     self.save(update_fields=["status"])