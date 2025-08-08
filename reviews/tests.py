from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import User
from books.models import Book
from .models import Review

User = get_user_model()

class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@test.com', 
            password='password'
        )
        self.book = Book.objects.create(
            title="테스트 도서",
            author="테스트 저자",
            isbn="1234567890123",
            publisher="테스트 출판사",
            category="소설"
        )
    
    def test_review_creation(self):
        """리뷰 생성 테스트"""
        review = Review.objects.create(
            user=self.user,
            book=self.book,
            content="정말 좋은 책입니다!",
            rating=5
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.content, "정말 좋은 책입니다!")
        self.assertEqual(str(review), "테스트 도서 - testuser")
    
    def test_rating_stars(self):
        """별점 표시 테스트"""
        review = Review.objects.create(
            user=self.user,
            book=self.book,
            content="보통입니다",
            rating=3
        )
        self.assertEqual(review.get_rating_stars(), "★★★☆☆")
    
    def test_unique_review_per_user_book(self):
        """한 사용자당 한 책에 하나의 리뷰만 허용 테스트"""
        Review.objects.create(
            user=self.user,
            book=self.book,
            content="첫 번째 리뷰",
            rating=4
        )
        
        # 같은 사용자가 같은 책에 또 다른 리뷰 작성 시도
        with self.assertRaises(Exception):
            Review.objects.create(
                user=self.user,
                book=self.book,
                content="두 번째 리뷰",
                rating=5
            )

class ReviewViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@test.com', 
            password='password'
        )
        self.book = Book.objects.create(
            title="테스트 도서",
            author="테스트 저자",
            isbn="1234567890123",
            publisher="테스트 출판사",
            category="소설"
        )
    
    def test_book_detail_view(self):
        """도서 상세 페이지 테스트"""
        response = self.client.get(reverse('reviews:book_detail', args=[self.book.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "테스트 도서")
    
    def test_create_review_requires_login(self):
        """리뷰 작성은 로그인이 필요함 테스트"""
        response = self.client.get(reverse('reviews:create_review', args=[self.book.id]))
        self.assertEqual(response.status_code, 302)  # 로그인 페이지로 리다이렉트
    
    def test_create_review_authenticated(self):
        """로그인된 사용자의 리뷰 작성 페이지 테스트"""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('reviews:create_review', args=[self.book.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_create_review_post(self):
        """리뷰 작성 POST 요청 테스트"""
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('reviews:create_review', args=[self.book.id]), {
            'rating': 5,
            'content': '정말 좋은 책입니다!'
        })
        self.assertEqual(response.status_code, 302)  # 리다이렉트
        self.assertTrue(Review.objects.filter(user=self.user, book=self.book).exists())
    
    def test_duplicate_review_prevention(self):
        """중복 리뷰 방지 테스트"""
        # 첫 번째 리뷰 작성
        Review.objects.create(
            user=self.user,
            book=self.book,
            content="첫 번째 리뷰",
            rating=4
        )
        
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('reviews:create_review', args=[self.book.id]))
        self.assertEqual(response.status_code, 302)  # 리다이렉트 (중복 리뷰 방지)
    
    def test_edit_own_review(self):
        """자신의 리뷰 수정 테스트"""
        review = Review.objects.create(
            user=self.user,
            book=self.book,
            content="원래 리뷰",
            rating=3
        )
        
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('reviews:edit_review', args=[review.id]), {
            'rating': 5,
            'content': '수정된 리뷰'
        })
        
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.content, '수정된 리뷰')
    
    def test_delete_own_review(self):
        """자신의 리뷰 삭제 테스트"""
        review = Review.objects.create(
            user=self.user,
            book=self.book,
            content="삭제할 리뷰",
            rating=3
        )
        
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('reviews:delete_review', args=[review.id]))
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.filter(id=review.id).exists())

class ReviewAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@test.com', 
            password='password'
        )
        self.book = Book.objects.create(
            title="테스트 도서",
            author="테스트 저자",
            isbn="1234567890123",
            publisher="테스트 출판사",
            category="소설"
        )
    
    def test_review_list_api(self):
        """리뷰 목록 API 테스트"""
        Review.objects.create(
            user=self.user,
            book=self.book,
            content="API 테스트 리뷰",
            rating=4
        )
        
        response = self.client.get(reverse('reviews:api_review_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_review_create_api_requires_auth(self):
        """리뷰 작성 API 인증 필요 테스트"""
        response = self.client.post(reverse('reviews:api_review_create'), {
            'book': self.book.id,
            'content': '인증 없는 리뷰',
            'rating': 3
        })
        # 인증되지 않은 사용자는 401 또는 403 응답
        self.assertIn(response.status_code, [401, 403])