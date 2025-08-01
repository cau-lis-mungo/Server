from django.db import models
from users.models import User
from books.models import Book

# Create your models here.
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews') # 사용자
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews') # 도서
    content = models.TextField() # 리뷰 내용
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.book.title} - {self.user.username}"