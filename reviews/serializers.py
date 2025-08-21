from django.db import IntegrityError, transaction
from rest_framework import serializers
from .models import Review
from books.models import Book

class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "book", "book_title", "user_username", "content", "created_at"] # rating
        read_only_fields = ['created_at', 'updated_at']

    # def create(self, validated_data):
    #     validated_data['user'] = self.context['request'].user
    #     return super().create(validated_data)
    
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'publisher', 'category']

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['book', 'content'] # rating
    
    # def validate_rating(self, value):
    #     if not (1 <= value <= 5):
    #         raise serializers.ValidationError("평점은 1~5 사이여야 합니다.")
    #     return value
    
    def validate(self, data):
        user = self.context["request"].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"message": "로그인이 필요합니다."})
        
        book = data.get("book")
        if Review.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError({"message": "이미 이 책에 대한 리뷰를 작성하셨습니다."})
        return data

class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['content'] # rating
    
    # def validate_rating(self, value):
    #     if not (1 <= value <= 5):
    #         raise serializers.ValidationError({"message": "평점은 1~5 사이여야 합니다."})
    #     return value