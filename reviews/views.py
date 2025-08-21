from django.db.models import QuerySet
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer

class IsOwnerOrReadOnly(permissions.BasePermission): # POST, PUT, PATCH, DELETE는 작성자나 스태프만 허용
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == getattr(request.user, "id", None) or request.user.is_staff

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related("user", "book").all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    serializer_class = ReviewSerializer

    # 필터/검색/정렬
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["book", "user"] # rating
    search_fields = ["content", "book__title", "user__username"]
    ordering_fields = ["created_at"] # rating
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        user_id = self.request.query_params.get("userId")
        book_id = self.request.query_params.get("bookId")
        if user_id:
            qs = qs.filter(user_id=user_id)
        if book_id:
            qs = qs.filter(book_id=book_id)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return ReviewCreateSerializer
        if self.action in ["update", "partial_update"]:
            return ReviewUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)