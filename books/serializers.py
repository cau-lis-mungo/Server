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

# 상세 조회
class BookDetailSerializer(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True) # 제목
    image = serializers.ImageField(read_only=True) # 이미지
    author = serializers.CharField(read_only=True) # 저자
    edition = serializers.CharField(read_only=True) # 판사항
    callnumber = serializers.CharField(read_only=True) # 청구기호

    # Marc
    publication = serializers.CharField(source='marc.field_260', read_only=True) # 발행사항
    physical = serializers.CharField(source='marc.field_300', read_only=True) # 형태사항
    marc = serializers.JSONField(source='marc.data', read_only=True) # 전체 MARC

    class Meta:
        model = Book
        fields = [
            'title', 'image', 'author', 'edition',
            'publication', 'physical',
            'callnumber', 'marc',
        ]