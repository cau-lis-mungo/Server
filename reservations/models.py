# reservations/models.py
from django.conf import settings
from django.db import models
from books.models import Book

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', '예약중'),
        ('CANCELED', '예약취소'),
        ('EXPIRED', '예약만료'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    reservation_date = models.DateTimeField(auto_now_add=True) # 예약일
    due_date = models.DateField(null=True, blank=True) # 예약만료일
    cancel_date = models.DateTimeField(null=True, blank=True) # 예약취소일

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE',
    )

    class Meta:
        ordering = ['-reservation_date']

    def __str__(self):
        return f"{self.user} → {self.book} ({self.status})"