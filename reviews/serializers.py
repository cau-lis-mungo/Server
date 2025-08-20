from rest_framework import serializers
from .models import Review
from books.models import Book

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user', 'review_date']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'publisher', 'category']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['book', 'content', 'rating']
    
    def validate(self, data):
        user = self.context['request'].user
        book = data['book']
        
        # 이미 리뷰를 작성했는지 확인
        if Review.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError("이미 이 책에 대한 리뷰를 작성하셨습니다.")
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['content', 'rating']