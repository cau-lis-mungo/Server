from django.db import models
from django.conf import settings
# from datetime import date
from django.utils import timezone
from books.models import Book

# Create your models here.
def _rental_days() -> int:
    return getattr(settings, "RENTAL_DAYS", 14)  # 기본 14일

def _rental_limit() -> int:
    return getattr(settings, "RENTAL_LIMIT_PER_USER", 5)

class Rental(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    
    rental_date = models.DateField(auto_now_add=True) # 대출일
    due_date = models.DateField() # 반납예정일
    return_date = models.DateField(null=True, blank=True) # 반납일
    is_returned = models.BooleanField(default=False) # 반납여부

    class Meta:
        # 같은 책에 대한 대출 1건만 허용
        constraints = [
            models.UniqueConstraint(
                fields=["book", "is_returned"],
                condition=models.Q(is_returned=False),
                name="uq_active_rental_per_book"
            )
        ]

    @property
    def is_overdue(self): # 연체여부
        return not self.is_returned and self.due_date < timezone.localdate()

    @property
    def overdue_days(self): # 연체일
        if self.is_overdue:
            return (timezone.localdate() - self.due_date).days
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({'반납' if self.is_returned else '대출중'})"