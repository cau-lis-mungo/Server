from django.apps import AppConfig

class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'
    verbose_name = '도서 리뷰'
    
    def ready(self):
        """앱이 준비되었을 때 실행되는 코드"""
        # 시그널 등록 