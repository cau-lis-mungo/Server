from django.db import models
from django.conf import settings

# Create your models here.
class Book(models.Model):
    BOOK_STATUS_CHOICES = [
        ('대출가능', '대출가능'),
        ('예약중', '예약중'),
        ('대출불가', '대출불가'),
    ]

    book_code = models.CharField(max_length=30, unique=True)  # 장서등록번호
    title = models.CharField(max_length=200, null=True, blank=True)  # 표제
    author = models.CharField(max_length=100, null=True, blank=True)  # 저자사항
    isbn = models.CharField(max_length=20, null=True, blank=True)  # ISBN
    callnumber = models.CharField(max_length=50, null=True, blank=True)  # 청구기호
    # marc = models.TextField(null=True, blank=True)  # 마크
    edition = models.CharField(max_length=100, null=True, blank=True)  # 판사항
    notes = models.TextField(null=True, blank=True)  # 주기사항
    desc = models.TextField(null=True, blank=True)  # 총서사항
    book_status = models.CharField(max_length=20, choices=BOOK_STATUS_CHOICES, default='대출가능')  # 도서 상태
    image = models.ImageField(upload_to='book_images/', null=True, blank=True)  # 표지 이미지

    liked_users = models.ManyToManyField( # 좋아요
        settings.AUTH_USER_MODEL,
        related_name='liked_books',
        blank=True
    )

    def __str__(self):
        return f"{self.title} ({self.book_code})"

class Marc(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='marc_info')
    content = models.TextField() # 임시 필드

    def __str__(self):
        return f"Marc info for {self.book.title}"
