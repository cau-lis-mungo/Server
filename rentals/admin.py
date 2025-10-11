from django.contrib import admin
from .models import Rental, BorrowPenalty

# Register your models here.
admin.site.register(Rental)
admin.site.register(BorrowPenalty)

class BorrowPenaltyAdmin(admin.ModelAdmin):
    list_display = ("user", "penalty_until")

# from django.utils.html import format_html
# from django.urls import reverse
# from django.utils.safestring import mark_safe
# from .models import Rental


# @admin.register(Rental)
# class RentalAdmin(admin.ModelAdmin):
#     list_display = [
#         'id', 'user_link', 'book_link', 'rental_date', 
#         'due_date', 'return_date', 'status_display', 
#         'overdue_display', 'days_display'
#     ]
#     list_filter = [
#         'is_returned', 'rental_date', 'due_date', 
#         'return_date'
#     ]
#     search_fields = [
#         'user__username', 'user__first_name', 'user__last_name',
#         'book__title', 'book__author', 'book__isbn'
#     ]
#     date_hierarchy = 'rental_date'
#     ordering = ['-rental_date']
#     readonly_fields = ['rental_date', 'is_overdue_display', 'overdue_days_display']
    
#     fieldsets = (
#         ('기본 정보', {
#             'fields': ('user', 'book')
#         }),
#         ('대출 정보', {
#             'fields': ('rental_date', 'due_date', 'return_date', 'is_returned')
#         }),
#         ('연체 정보', {
#             'fields': ('is_overdue_display', 'overdue_days_display'),
#             'classes': ('collapse',)
#         }),
#     )

#     def user_link(self, obj):
#         """사용자 링크"""
#         if obj.user:
#             url = reverse('admin:auth_user_change', args=[obj.user.pk])
#             return format_html('<a href="{}">{}</a>', url, obj.user.username)
#         return '-'
#     user_link.short_description = '사용자'
#     user_link.admin_order_field = 'user__username'

#     def book_link(self, obj):
#         """도서 링크"""
#         if obj.book:
#             url = reverse('admin:books_book_change', args=[obj.book.pk])
#             return format_html('<a href="{}">{}</a>', url, obj.book.title)
#         return '-'
#     book_link.short_description = '도서'
#     book_link.admin_order_field = 'book__title'

#     def status_display(self, obj):
#         """반납 상태 표시"""
#         if obj.is_returned:
#             return format_html(
#                 '<span style="color: green; font-weight: bold;">반납완료</span>'
#             )
#         else:
#             return format_html(
#                 '<span style="color: orange; font-weight: bold;">대출중</span>'
#             )
#     status_display.short_description = '상태'
#     status_display.admin_order_field = 'is_returned'

#     def overdue_display(self, obj):
#         """연체 상태 표시"""
#         if obj.is_overdue:
#             return format_html(
#                 '<span style="color: red; font-weight: bold;">연체</span>'
#             )
#         return format_html(
#             '<span style="color: green;">정상</span>'
#         )
#     overdue_display.short_description = '연체여부'

#     def days_display(self, obj):
#         """일수 표시"""
#         if obj.is_overdue:
#             return format_html(
#                 '<span style="color: red; font-weight: bold;">{} 일</span>',
#                 obj.overdue_days
#             )
#         return '-'
#     days_display.short_description = '연체일수'

#     def is_overdue_display(self, obj):
#         """읽기 전용 연체 상태"""
#         return obj.is_overdue
#     is_overdue_display.short_description = '연체 여부'
#     is_overdue_display.boolean = True

#     def overdue_days_display(self, obj):
#         """읽기 전용 연체일수"""
#         return obj.overdue_days
#     overdue_days_display.short_description = '연체 일수'

#     def get_queryset(self, request):
#         """쿼리셋 최적화"""
#         return super().get_queryset(request).select_related('user', 'book')

#     def save_model(self, request, obj, form, change):
#         """모델 저장 시 추가 로직"""
#         # 반납 처리 시 반납일 자동 설정
#         if obj.is_returned and not obj.return_date:
#             from datetime import date
#             obj.return_date = date.today()
#         elif not obj.is_returned:
#             obj.return_date = None
        
#         super().save_model(request, obj, form, change)

#     actions = ['mark_as_returned', 'mark_as_not_returned']

#     def mark_as_returned(self, request, queryset):
#         """선택된 대출을 반납 처리"""
#         from datetime import date
#         updated = queryset.filter(is_returned=False).update(
#             is_returned=True,
#             return_date=date.today()
#         )
#         self.message_user(
#             request, 
#             f'{updated}개의 대출이 반납 처리되었습니다.'
#         )
#     mark_as_returned.short_description = '선택된 항목을 반납 처리'

#     def mark_as_not_returned(self, request, queryset):
#         """선택된 대출을 미반납 처리"""
#         updated = queryset.filter(is_returned=True).update(
#             is_returned=False,
#             return_date=None
#         )
#         self.message_user(
#             request, 
#             f'{updated}개의 대출이 미반납 처리되었습니다.'
#         )
#     mark_as_not_returned.short_description = '선택된 항목을 미반납 처리'