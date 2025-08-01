from django.urls import path, include
from .views import BookLikedView, BookViewSet
from rest_framework.routers import DefaultRouter # ViewSet을 자동으로 URL에 연결

router = DefaultRouter()
router.register(r'', BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:book_id>/like/', BookLikedView.as_view(), name='book-liked'),
]