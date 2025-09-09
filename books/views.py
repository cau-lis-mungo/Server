from django.shortcuts import render
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status, viewsets, filters, permissions, serializers
from .models import Book
from reservations.models import Reservation
from .serializers import BookSerializer, BookDetailSerializer
from reservations.serializers import ReservationSerializer
from .filters import MinLengthSearchFilter


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
        if book.liked_users.filter(pk=user.pk).exists():
            book.liked_users.remove(user)
            return Response({"message": "좋아요 취소됨"}, status=status.HTTP_200_OK)
        else:
            book.liked_users.add(user)
            return Response({"message": "좋아요 등록됨"}, status=status.HTTP_201_CREATED)

# 목록 + 상세
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    # serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # filter_backends = [filters.SearchFilter]
    filter_backends = [MinLengthSearchFilter]
    search_fields = ['=isbn', '=book_code','title', 'author', '^publisher']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookDetailSerializer
        return BookSerializer
    
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="reserve")
    def reserve(self, request, pk=None):
        book = self.get_object()
        user = request.user

        if Reservation.objects.active().filter(user=user, book=book).exists():
            raise serializers.ValidationError({"message": "이미 예약하셨습니다."})

        instance = Reservation(user=user, book=book)
        try:
            instance.full_clean()
        except ValidationError as e:
            detail = getattr(e, "message_dict", None) or {"message": e.messages}
            return Response(detail, status=status.HTTP_400_BAD_REQUEST)

        instance.save()
        return Response(ReservationSerializer(instance, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)