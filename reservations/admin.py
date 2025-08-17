from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'status', 'created_at', 'due_date', 'canceled_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'book__title')
