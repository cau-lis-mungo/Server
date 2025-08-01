from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Book

# Create your views here.
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