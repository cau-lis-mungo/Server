from rest_framework import serializers
from .models import Rental

class RentalSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()

    class Meta:
        model = Rental
        fields = '__all__'
        # fields = ['id', 'user', 'book', 'rental_date', 'due_date', 'return_date', 'is_returned', 'is_overdue', 'overdue_days']

    def get_is_overdue(self, obj):
        return obj.is_overdue

    def get_overdue_days(self, obj):
        return obj.overdue_days
