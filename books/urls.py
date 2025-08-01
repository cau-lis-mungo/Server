from django.urls import path
from .views import BookLikedView

urlpatterns = [
    path('<int:book_id>/like/', BookLikedView.as_view(), name='book-liked'),
]