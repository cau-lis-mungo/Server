from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
from books.models import Book
from .models import Rental


class RentalModelTest(TestCase):
    """Rental 모델 테스트"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.book = Book.objects.create(
            title='테스트 도서',
            author='테스트 저자',
            isbn='1234567890',
            publication_date='2023-01-01'
        )
        
        self.rental = Rental.objects.create(
            user=self.user,
            book=self.book,
            due_date=date.today() + timedelta(days=14)
        )

    def test_rental_creation(self):
        """대출 객체 생성 테스트"""
        self.assertEqual(self.rental.user, self.user)
        self.assertEqual(self.rental.book, self.book)
        self.assertEqual(self.rental.rental_date, date.today())
        self.assertFalse(self.rental.is_returned)
        self.assertIsNone(self.rental.return_date)

    def test_is_overdue_property(self):
        """연체 여부 확인 테스트"""
        # 정상적인 경우
        self.assertFalse(self.rental.is_overdue)
        
        # 연체된 경우
        self.rental.due_date = date.today() - timedelta(days=1)
        self.rental.save()
        self.assertTrue(self.rental.is_overdue)
        
        # 반납된 경우
        self.rental.is_returned = True
        self.rental.return_date = date.today()
        self.rental.save()
        self.assertFalse(self.rental.is_overdue)

    def test_overdue_days_property(self):
        """연체일수 계산 테스트"""
        # 정상적인 경우
        self.assertEqual(self.rental.overdue_days, 0)
        
        # 3일 연체된 경우
        self.rental.due_date = date.today() - timedelta(days=3)
        self.rental.save()
        self.assertEqual(self.rental.overdue_days, 3)

    def test_str_method(self):
        """문자열 표현 테스트"""
        expected = f"{self.user.username} - {self.book.title} (대출중)"
        self.assertEqual(str(self.rental), expected)
        
        self.rental.is_returned = True
        self.rental.save()
        expected = f"{self.user.username} - {self.book.title} (반납)"
        self.assertEqual(str(self.rental), expected)


class RentalAPITest(APITestCase):
    """Rental API 테스트"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.book1 = Book.objects.create(
            title='테스트 도서 1',
            author='테스트 저자 1',
            isbn='1234567890',
            publication_date='2023-01-01'
        )
        
        self.book2 = Book.objects.create(
            title='테스트 도서 2',
            author='테스트 저자 2',
            isbn='0987654321',
            publication_date='2023-02-01'
        )
        
        self.client = APIClient()

    def test_rent_book_success(self):
        """도서 대출 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/rentals/rent_book/', {
            'book_id': self.book1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Rental.objects.filter(user=self.user, book=self.book1).exists())

    def test_rent_already_rented_book(self):
        """이미 대출된 도서 대출 시도 테스트"""
        # 먼저 도서 대출
        Rental.objects.create(
            user=self.user,
            book=self.book1,
            due_date=date.today() + timedelta(days=14)
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/rentals/rent_book/', {
            'book_id': self.book1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_book_success(self):
        """도서 반납 성공 테스트"""
        rental = Rental.objects.create(
            user=self.user,
            book=self.book1,
            due_date=date.today() + timedelta(days=14)
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(f'/api/rentals/{rental.id}/return_book/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rental.refresh_from_db()
        self.assertTrue(rental.is_returned)
        self.assertEqual(rental.return_date, date.today())

    def test_return_already_returned_book(self):
        """이미 반납된 도서 반납 시도 테스트"""
        rental = Rental.objects.create(
            user=self.user,
            book=self.book1,
            due_date=date.today() + timedelta(days=14),
            is_returned=True,
            return_date=date.today()
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(f'/api/rentals/{rental.id}/return_book/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_rentals(self):
        """내 대출 목록 조회 테스트"""
        Rental.objects.create(
            user=self.user,
            book=self.book1,
            due_date=date.today() + timedelta(days=14)
        )
        
        # 다른 사용자의 대출
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass'
        )
        Rental.objects.create(
            user=other_user,
            book=self.book2,
            due_date=date.today() + timedelta(days=14)
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/rentals/my_rentals/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['book'], self.book1.id)

    def test_overdue_books(self):
        """연체 도서 목록 조회 테스트"""
        # 연체된 대출
        overdue_rental = Rental.objects.create(
            user=self.user,
            book=self.book1,
            due_date=date.today() - timedelta(days=3)
        )
        
        # 정상 대출
        normal_rental = Rental.objects.create(
            user=self.user,
            book=self.book2,
            due_date=date.today() + timedelta(days=7)
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/rentals/overdue_books/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], overdue_rental.id)

    def test_statistics_admin_only(self):
        """통계 정보 관리자 전용 테스트"""
        # 일반 사용자로 접근
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/rentals/statistics/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # 관리자로 접근
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/rentals/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_rentals', response.data)

    def test_unauthenticated_access(self):
        """인증되지 않은 접근 테스트"""
        response = self.client.get('/api/rentals/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RentalAdminTest(TestCase):
    """RentalAdmin 테스트"""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.book = Book.objects.create(
            title='테스트 도서',
            author='테스트 저자',
            isbn='1234567890',
            publication_date='2023-01-01'
        )
        
        self.rental = Rental.objects.create(
            user=self.user,
            book=self.book,
            due_date=date.today() + timedelta(days=14)
        )

    def test_admin_actions_mark_as_returned(self):
        """관리자 액션: 반납 처리 테스트"""
        from django.contrib.admin.sites import AdminSite
        from .admin import RentalAdmin
        
        site = AdminSite()
        admin = RentalAdmin(Rental, site)
        
        queryset = Rental.objects.filter(id=self.rental.id)
        request = type('MockRequest', (), {'user': self.admin_user})()
        
        admin.mark_as_returned(request, queryset)
        
        self.rental.refresh_from_db()
        self.assertTrue(self.rental.is_returned)
        self.assertEqual(self.rental.return_date, date.today())