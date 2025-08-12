from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet

# DRF Router 설정
router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet)

app_name = 'reviews'

urlpatterns = [
    # API URL (ViewSet 기반)
    path('api/', include(router.urls)),
    
    # 템플릿 기반 URL
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book/<int:book_id>/review/create/', views.create_review, name='create_review'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('reviews/', views.review_list, name='review_list'),
    path('user/<int:user_id>/reviews/', views.user_reviews, name='user_reviews'),
    
    # AJAX URL
    path('ajax/book/<int:book_id>/review/create/', views.ajax_create_review, name='ajax_create_review'),
    path('ajax/review/<int:review_id>/update/', views.ajax_update_review, name='ajax_update_review'),
]