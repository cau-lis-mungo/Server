from django.apps import AppConfig


class RentalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rentals' 
    verbose_name = '도서 대출관리'

    def ready(self):
        # import rentals.signals
        pass
