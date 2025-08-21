from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status, viewsets, filters
from .models import Book
from .serializers import BookSerializer, BookDetailSerializer

# Create your views here.
# 좋아요
class BookLikedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "책을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user in book.liked_users.all():
            book.liked_users.remove(user)
            return Response({"message": "좋아요 취소됨"}, status=status.HTTP_200_OK)
        else:
            book.liked_users.add(user)
            return Response({"message": "좋아요 등록됨"}, status=status.HTTP_201_CREATED)

# 목록 + 상세
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'author', 'isbn']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookDetailSerializer
        return BookSerializer