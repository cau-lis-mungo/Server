from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import date, timedelta
from django.shortcuts import get_object_or_404
from books import serializers
from books.models import Book
from .models import Rental
from .serializers import RentalSerializer


class RentalViewSet(viewsets.ModelViewSet):
    
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer
    permission_classes = [IsAuthenticated]
    
    # 필터링 및 검색 설정
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_returned', 'user', 'book']
    search_fields = ['book__title', 'book__author', 'user__username']
    ordering_fields = ['rental_date', 'due_date', 'return_date']
    ordering = ['-rental_date']

    def get_queryset(self):
        """쿼리셋 최적화"""
        return self.queryset.select_related('user', 'book').order_by('-rental_date')

    def perform_create(self, serializer):
        """대출 생성 시 추가 로직"""
        book = serializer.validated_data['book']
        
        # 이미 대출 중인 도서 확인
        if Rental.objects.filter(book=book, is_returned=False).exists():
            raise serializers.ValidationError("이미 대출 중인 도서입니다.")
        
        # 반납 예정일 설정 (14일 후)
        due_date = date.today() + timedelta(days=14)
        serializer.save(user=self.request.user, due_date=due_date)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        """
        도서 반납 처리
        POST /api/rentals/{id}/return_book/
        """
        rental = self.get_object()
        
        if rental.is_returned:
            return Response(
                {'error': '이미 반납된 도서입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rental.is_returned = True
        rental.return_date = date.today()
        rental.save()
        
        serializer = self.get_serializer(rental)
        return Response({
            'message': '도서가 성공적으로 반납되었습니다.',
            'rental': serializer.data
        })

    @action(detail=False, methods=['get'])
    def my_rentals(self, request):
        """
        현재 사용자의 대출 목록
        GET /api/rentals/my_rentals/
        """
        rentals = self.get_queryset().filter(user=request.user)
        
        # 추가 필터링
        is_returned = request.query_params.get('is_returned', None)
        if is_returned is not None:
            is_returned = is_returned.lower() == 'true'
            rentals = rentals.filter(is_returned=is_returned)
        
        page = self.paginate_queryset(rentals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(rentals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue_books(self, request):
        """
        연체 도서 목록
        GET /api/rentals/overdue_books/
        """
        overdue_rentals = self.get_queryset().filter(
            is_returned=False,
            due_date__lt=date.today()
        )
        
        # 관리자가 아닌 경우 본인의 연체 도서만 조회
        if not request.user.is_staff:
            overdue_rentals = overdue_rentals.filter(user=request.user)
        
        page = self.paginate_queryset(overdue_rentals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(overdue_rentals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def rent_book(self, request):
        """
        도서 대출 (도서 ID로)
        POST /api/rentals/rent_book/
        Body: {"book_id": 1}
        """
        book_id = request.data.get('book_id')
        if not book_id:
            return Response(
                {'error': 'book_id가 필요합니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {'error': '존재하지 않는 도서입니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 이미 대출 중인 도서 확인
        if Rental.objects.filter(book=book, is_returned=False).exists():
            return Response(
                {'error': '이미 대출 중인 도서입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 사용자가 이미 같은 도서를 대출 중인지 확인
        if Rental.objects.filter(user=request.user, book=book, is_returned=False).exists():
            return Response(
                {'error': '이미 대출 중인 도서입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 대출 생성
        rental = Rental.objects.create(
            user=request.user,
            book=book,
            due_date=date.today() + timedelta(days=14)
        )
        
        serializer = self.get_serializer(rental)
        return Response({
            'message': '도서가 성공적으로 대출되었습니다.',
            'rental': serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        대출 통계 정보
        GET /api/rentals/statistics/
        """
        if not request.user.is_staff:
            return Response(
                {'error': '관리자만 접근 가능합니다.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        total_rentals = Rental.objects.count()
        active_rentals = Rental.objects.filter(is_returned=False).count()
        overdue_rentals = Rental.objects.filter(
            is_returned=False,
            due_date__lt=date.today()
        ).count()
        
        return Response({
            'total_rentals': total_rentals,
            'active_rentals': active_rentals,
            'returned_rentals': total_rentals - active_rentals,
            'overdue_rentals': overdue_rentals,
            'overdue_rate': (overdue_rentals / active_rentals * 100) if active_rentals > 0 else 0
        })