from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from users.models import User
from books.models import Book

# Create your models here.
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews') # 사용자
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews') # 도서
    content = models.TextField(verbose_name="리뷰 내용") # 리뷰 내용
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="평점",
        default=5
    )  # 1-5점 평점
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('book', 'user')  # 한 사용자당 한 책에 하나의 리뷰만
        ordering = ['-created_at']  # 최신순으로 정렬
        verbose_name = "리뷰"
        verbose_name_plural = "리뷰들"

    def __str__(self):
        return f"{self.book.title} - {self.user.username}"

# def get_average_rating(self):
#     """평균 평점 계산"""
#     reviews = self.reviews.all()
#     if reviews:
#         total_rating = sum([review.rating for review in reviews])
#         return round(total_rating / len(reviews), 1)
#     return 0

# def get_review_count(self):
#     """리뷰 개수 반환"""
#     return self.reviews.count()

# def get_rating_distribution(self):
#     """평점별 분포 계산"""
#     reviews = self.reviews.all()
#     distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
#     for review in reviews:
#         distribution[review.rating] += 1
#     return distribution