from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from .models import Rental, BorrowPenalty
from reservations.models import Reservation
from books.models import Book, BookStatus

# 대출가능일
def _rental_days() -> int:
    return getattr(settings, "RENTAL_DAYS", 14)
# 대출가능권수
def _rental_limit() -> int:
    return getattr(settings, "RENTAL_LIMIT_PER_USER", 5)

class BookBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "book_code", "image_url", "book_status",)

class RentalListSerializer(serializers.ModelSerializer):
    book = BookBriefSerializer(read_only=True)

    class Meta:
        model = Rental
        fields = ("id", "book",)

class RentalSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()

    class Meta:
        model = Rental
        fields = "__all__"
        read_only_fields = (
            "id", "user", "rental_date", "return_date", "is_returned", "due_date",
            "is_overdue", "overdue_days",
        )

    def get_is_overdue(self, obj):
        base = obj.return_date or timezone.localdate()
        return base > obj.due_date

    def get_overdue_days(self, obj):
        base = obj.return_date or timezone.localdate()
        return max(0, (base - obj.due_date).days)

# 대출 생성
class RentalCreateSerializer(serializers.ModelSerializer):
    code = serializers.CharField(label="장서등록번호", write_only=True)

    class Meta:
        model = Rental
        fields = ("code",)

    def validate(self, attrs):
        user = self.context["request"].user
        code = attrs["code"].strip()
        today = timezone.localdate()

        # 책 찾기
        try:
            book = Book.objects.get(book_code=code)
        except Book.DoesNotExist:
            raise serializers.ValidationError({"message": "해당 코드의 도서를 찾을 수 없습니다."})
        
        # 패널티 중이면 대출 불가
        penalty = getattr(user, "borrow_penalty", None)
        if penalty and penalty.in_penalty:
            raise serializers.ValidationError({
                "message": f"연체로 인해 {penalty.penalty_until}까지 대출이 불가합니다."
            })

        # 연체 중 도서 존재하면 불가
        if Rental.objects.filter(user=user, is_returned=False, due_date__lt=today).exists():
            raise serializers.ValidationError({"message": "연체 중인 도서가 있어 대출이 불가합니다."})

        # 대출 한도 초과 시 대출 불가
        active_count = Rental.objects.filter(user=user, is_returned=False).count()
        if active_count >= _rental_limit():
            raise serializers.ValidationError({"message" : "대출 한도를 초과했습니다."})

        # 미반납 도서 대출 불가
        if Rental.objects.filter(book=book, is_returned=False).exists():
            raise serializers.ValidationError({"message" : "이미 대출 중인 도서입니다."})
        
        # 책 상태 확인
        if getattr(book, "book_status",  BookStatus.AVAILABLE) != BookStatus.AVAILABLE:
            raise serializers.ValidationError({"message" : "이 도서는 현재 대출할 수 없습니다."})
        
        self.context["book"] = book
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        book = self.context["book"]

        due_date = timezone.localdate() + timedelta(days=_rental_days())
        rental = Rental.objects.create(user=user, book=book, due_date=due_date, return_date = None, is_returned = False)

        # 책 상태 변경
        if hasattr(book, "book_status") and book.book_status != BookStatus.RENTED:
            book.book_status = BookStatus.RENTED
            book.save(update_fields=["book_status"])
        return rental

# 대출 수정 (반납)
class RentalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ("is_returned",)
        extra_kwargs = {
            "is_returned": {"required": True}
        }

    def validate(self, attrs):
        instance: Rental = self.instance
        want_return = attrs.get("is_returned")

        # 반납만 허용
        if want_return is not True:
            raise serializers.ValidationError({"message" : "이미 반납되었습니다."})
        if instance.is_returned:
            raise serializers.ValidationError({"message" : "이미 반납되었습니다."})
        return attrs

    @transaction.atomic
    def update(self, instance: Rental, validated_data):
        # 반납
        instance.is_returned = True
        instance.return_date = timezone.localdate()
        instance.save(update_fields=["is_returned", "return_date"])

        # 연체
        if instance.return_date > instance.due_date:
            overdue_days = (instance.return_date - instance.due_date).days
            penalty, _ = BorrowPenalty.objects.get_or_create(user=instance.user)
            penalty.extend_by_days(overdue_days)

        # 예약
        book = instance.book
        RES_DAYS = getattr(settings, "RESERVATION_DAYS", 3)

        try:
            target = (
                Reservation.objects.active()
                .filter(book=book)
                .order_by("reservation_date")
                .first()
            )
        except Exception:
            target = None

        if target:
            # 예약만기일 부여
            target.due_date = timezone.localdate() + timedelta(days=RES_DAYS)
            target.save(update_fields=["due_date"])

            # 예약자 있으면
            if hasattr(book, "book_status") and book.book_status != BookStatus.RESERVED:
                book.book_status = BookStatus.RESERVED
                book.save(update_fields=["book_status"])
        else:
            # 예약자 없으면
            if hasattr(book, "book_status") and book.book_status != BookStatus.AVAILABLE:
                book.book_status = BookStatus.AVAILABLE
                book.save(update_fields=["book_status"])

        return instance

# 대출 조회
class RentalStatusListSerializer(serializers.ModelSerializer):
    book = BookBriefSerializer(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()

    class Meta:
        model = Rental
        fields = (
            "id",
            "book",
            "rental_date",
            "due_date",
            "return_date",
            "is_returned",
            "is_overdue",
            "overdue_days",
        )
        read_only_fields = fields

    def get_is_overdue(self, obj):
        base = obj.return_date or timezone.localdate()
        return base > obj.due_date

    def get_overdue_days(self, obj):
        base = obj.return_date or timezone.localdate()
        return max(0, (base - obj.due_date).days)