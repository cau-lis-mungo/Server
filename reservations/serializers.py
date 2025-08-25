from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Reservation
from books.models import Book

class BookBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "book_code", "book_status")

# 예약 생성
class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["book"]
    
    def validate(self, attrs):
        user = self.context["request"].user
        book = attrs["book"]

        if Reservation.objects.filter(user=user, book=book, status="ACTIVE").exists():
            raise serializers.ValidationError({"message": "이미 예약하셨습니다."})
        return attrs

    # def create(self, validated_data):
    #     user = self.context["request"].user
    #     # 인스턴스 만들고 clean()으로 검증
    #     instance = Reservation(user=user, **validated_data)
    #     instance.full_clean()
    #     instance.save()
    #     return instance

    def create(self, validated_data):
        user = self.context["request"].user
        instance = Reservation(user=user, **validated_data)
        try:
            instance.full_clean()   # clean() + 필드 유효성
        except DjangoValidationError as e:
            # DRF가 이해하는 ValidationError로 변환 (400 반환)
            detail = getattr(e, "message_dict", None) or {"message": e.messages}
            raise serializers.ValidationError(detail)
        instance.save()
        return instance

# 예약 조회
class ReservationSerializer(serializers.ModelSerializer):
    # book = BookBriefSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"
        read_only_fields = ("book", "user", "reservation_date", "due_date", "cancel_date", "status")