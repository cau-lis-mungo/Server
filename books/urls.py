from django.urls import path, include
from .views import BookLikedView, BookViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:book_id>/like/', BookLikedView.as_view(), name='book-liked'),
]