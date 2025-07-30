from django.db import models
from users.models import User
from books.models import Book
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 사용자
    book = models.ForeignKey(Book, on_delete=models.CASCADE) # 도서
    reservation_date = models.DateField(auto_now_add=True) # 예약일
    reservation_due_date = models.DateField() # 예약만기일

    def save(self, *args, **kwargs):
        if not self.reservation_due_date:
            self.reservation_due_date = self.reservation_date + timedelta(days=7)  # 1주일 유지
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} → {self.book.title}"