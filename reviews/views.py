from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import OrderingFilter
from django.db.models import QuerySet

from .models import Review
from .serializers import ReviewSerializer
from .pagination import SizedPageNumberPagination

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
