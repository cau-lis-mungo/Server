from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    # like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'publisher',
            'callnumber',
            'location',
            'image',
            # 'liked_count', # 좋아요 개수
            'is_liked', # 좋아요 여부
            'book_status'
        ]

    # def get_like_count(self, obj):
    #     return obj.liked_users.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user in obj.liked_users.all()
        return False