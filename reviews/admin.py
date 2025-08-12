from django.contrib import admin
from .models import Review

# Register your models here.

admin.site.register(Review)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'get_rating_stars', 'created_at']
    list_filter = ['rating', 'created_at', 'book__category']
    search_fields = ['book__title', 'user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_rating_stars(self, obj):
        return obj.get_rating_stars()
    get_rating_stars.short_description = '별점'
    
    # 리스트에서 리뷰 내용 일부 표시
    def get_content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    get_content_preview.short_description = '리뷰 내용'
