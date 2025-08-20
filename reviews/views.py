from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .models import Review
from books.models import Book
from users.models import User
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    pagination_class = SizedPageNumberPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at"]  
    ordering = ["-created_at"]                  

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset().select_related("user", "book")

        user_id = self.request.query_params.get("userId")
        book_id = self.request.query_params.get("bookId")
        if user_id:
            qs = qs.filter(user_id=user_id)
        if book_id:
            qs = qs.filter(book_id=book_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# 템플릿 기반 뷰
def book_detail(request, book_id):
    """도서 상세 페이지 (리뷰 포함)"""
    book = get_object_or_404(Book, id=book_id)
    reviews = book.reviews.all()
    user_review = None
    
    if request.user.is_authenticated:
        try:
            user_review = Review.objects.get(book=book, user=request.user)
        except Review.DoesNotExist:
            pass
    
    # 평점별 분포 계산 (Book 모델에 메서드가 있다면)
    rating_distribution = {}
    if hasattr(book, 'get_rating_distribution'):
        rating_distribution = book.get_rating_distribution()
    
    context = {
        'book': book,
        'reviews': reviews,
        'user_review': user_review,
        'rating_distribution': rating_distribution,
    }
    
    return render(request, 'reviews/book_detail.html', context)

@login_required
def create_review(request, book_id):
    """리뷰 작성 페이지"""
    book = get_object_or_404(Book, id=book_id)
    
    # 이미 리뷰를 작성했는지 확인
    if Review.objects.filter(user=request.user, book=book).exists():
        messages.error(request, '이미 이 책에 대한 리뷰를 작성하셨습니다.')
        return redirect('book_detail', book_id=book.id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        content = request.POST.get('content')
        
        if rating and content:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    Review.objects.create(
                        book=book,
                        user=request.user,
                        rating=rating,
                        content=content
                    )
                    messages.success(request, '리뷰가 성공적으로 작성되었습니다.')
                    return redirect('book_detail', book_id=book.id)
                else:
                    messages.error(request, '평점은 1-5점 사이여야 합니다.')
            except ValueError:
                messages.error(request, '올바른 평점을 선택해주세요.')
        else:
            messages.error(request, '모든 필드를 입력해주세요.')
    
    return render(request, 'reviews/create_review.html', {'book': book})

@login_required
def edit_review(request, review_id):
    """리뷰 수정 페이지"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        content = request.POST.get('content')
        
        if rating and content:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    review.rating = rating
                    review.content = content
                    review.save()
                    messages.success(request, '리뷰가 성공적으로 수정되었습니다.')
                    return redirect('book_detail', book_id=review.book.id)
                else:
                    messages.error(request, '평점은 1-5점 사이여야 합니다.')
            except ValueError:
                messages.error(request, '올바른 평점을 선택해주세요.')
        else:
            messages.error(request, '모든 필드를 입력해주세요.')
    
    return render(request, 'reviews/edit_review.html', {'review': review})

@login_required
@require_POST
def delete_review(request, review_id):
    """리뷰 삭제"""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    book_id = review.book.id
    review.delete()
    messages.success(request, '리뷰가 삭제되었습니다.')
    return redirect('book_detail', book_id=book_id)

def review_list(request):
    """모든 리뷰 목록"""
    reviews = Review.objects.select_related('user', 'book').all()
    
    # 필터링
    book_id = request.GET.get('book')
    if book_id:
        reviews = reviews.filter(book_id=book_id)
    
    rating = request.GET.get('rating')
    if rating:
        reviews = reviews.filter(rating=rating)
    
    # 페이지네이션
    paginator = Paginator(reviews, 10)  # 한 페이지에 10개씩
    page = request.GET.get('page')
    reviews = paginator.get_page(page)
    
    return render(request, 'reviews/review_list.html', {'reviews': reviews})

def user_reviews(request, user_id):
    """특정 사용자의 리뷰 목록"""
    user = get_object_or_404(User, id=user_id)
    reviews = Review.objects.filter(user=user).select_related('book')
    
    # 페이지네이션
    paginator = Paginator(reviews, 10)
    page = request.GET.get('page')
    reviews = paginator.get_page(page)
    
    return render(request, 'reviews/user_reviews.html', {
        'reviews': reviews,
        'review_user': user
    })

# API 뷰 (REST Framework)
class ReviewListAPIView(generics.ListAPIView):
    """리뷰 목록 API"""
    queryset = Review.objects.select_related('user', 'book').all()
    serializer_class = ReviewSerializer
    
    def get_queryset(self):
        queryset = Review.objects.select_related('user', 'book').all()
        book_id = self.request.query_params.get('book', None)
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        return queryset

class ReviewCreateAPIView(generics.CreateAPIView):
    """리뷰 작성 API"""
    queryset = Review.objects.all()
    serializer_class = ReviewCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

class ReviewDetailAPIView(generics.RetrieveAPIView):
    """리뷰 상세 API"""
    queryset = Review.objects.select_related('user', 'book').all()
    serializer_class = ReviewSerializer

class ReviewUpdateAPIView(generics.UpdateAPIView):
    """리뷰 수정 API"""
    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

class ReviewDeleteAPIView(generics.DestroyAPIView):
    """리뷰 삭제 API"""
    queryset = Review.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

# AJAX 뷰
@login_required
@require_POST
def ajax_create_review(request, book_id):
    """AJAX 리뷰 작성"""
    book = get_object_or_404(Book, id=book_id)
    
    # 이미 리뷰를 작성했는지 확인
    if Review.objects.filter(user=request.user, book=book).exists():
        return JsonResponse({
            'success': False, 
            'error': '이미 이 책에 대한 리뷰를 작성하셨습니다.'
        })
    
    rating = request.POST.get('rating')
    content = request.POST.get('content')
    
    if not rating or not content:
        return JsonResponse({
            'success': False, 
            'error': '모든 필드를 입력해주세요.'
        })
    
    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            return JsonResponse({
                'success': False, 
                'error': '평점은 1-5점 사이여야 합니다.'
            })
        
        review = Review.objects.create(
            book=book,
            user=request.user,
            rating=rating,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'review': {
                'id': review.id,
                'rating': review.rating,
                # 'rating_stars': review.get_rating_stars(), # 이 줄은 models.py에 해당 메소드가 없을 수 있어 주석 처리합니다.
                'content': review.content,
                'user': review.user.username,
                'created_at': review.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
        
    except ValueError:
        return JsonResponse({
            'success': False, 
            'error': '올바른 평점을 선택해주세요.'
        })
    
@login_required
@require_POST
def ajax_update_review(request, review_id):
    """AJAX 리뷰 수정"""
    review = get_object_or_404(Review, id=review_id, user=request.user)

    rating = request.POST.get('rating')
    content = request.POST.get('content')

    if not rating or not content:
        return JsonResponse({
            'success': False,
            'error': '모든 필드를 입력해주세요.'
        })

    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            return JsonResponse({
                'success': False,
                'error': '평점은 1-5점 사이여야 합니다.'
            })

        review.rating = rating
        review.content = content
        review.save()
        
        return JsonResponse({
            'success': True,
            'review': {
                'id': review.id,
                'rating': review.rating,
                'content': review.content,
                'user': review.user.username,
                'updated_at': review.updated_at.strftime('%Y-%m-%d %H:%M')
            }
        })

    except ValueError:
        return JsonResponse({
            'success': False,
            'error': '올바른 평점을 선택해주세요.'
        })

def search_reviews(request):
    """리뷰 검색"""
    query = request.GET.get('q', '')
    reviews = Review.objects.select_related('user', 'book').all()
    
    if query:
        reviews = reviews.filter(
            Q(content__icontains=query) |
            Q(book__title__icontains=query) |
            Q(user__username__icontains=query)
        )
    
    paginator = Paginator(reviews, 20)
    page = request.GET.get('page')
    reviews = paginator.get_page(page)
    
    return render(request, 'reviews/search_results.html', {
        'reviews': reviews,
        'query': query
    })