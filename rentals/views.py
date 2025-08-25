from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Rental
from .serializers import (
    RentalSerializer, RentalCreateSerializer, RentalUpdateSerializer, RentalListSerializer,
)

class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user_id == request.user.id

class RentalViewSet(viewsets.ModelViewSet):
    queryset = Rental.objects.all().select_related("user", "book")
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        if not self.request.user.is_staff:
            return qs.filter(user=self.request.user)
        
        status_param = (self.request.query_params.get("status") or "").lower()
        if status_param == "active":
            qs = qs.filter(is_returned=False)
        elif status_param == "returned":
            qs = qs.filter(is_returned=True)

        # if self.request.query_params.get("all") == "true":
        #     return super().get_queryset()

        return qs

    def get_permissions(self):
        if self.action in ["retrieve", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminOrOwner()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return RentalCreateSerializer
        if self.action in ["update", "partial_update"]:
            return RentalUpdateSerializer
        if self.action == "list":
            return RentalListSerializer
        return RentalSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(RentalSerializer(instance).data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            {
                "message": "반납되었습니다.",
                "data": RentalSerializer(instance).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=["GET"], url_path="current")
    def current(self, request):
        qs = self.get_queryset().filter(is_returned=False).select_related("book")
        page = self.paginate_queryset(qs)
        ser_class = RentalListSerializer  # 목록 전용
        if page is not None:
            serializer = ser_class(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        serializer = ser_class(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # @transaction.atomic
    # def perform_return(self, rental):
    #     # 반납
    #     rental.returned_at = timezone.now()
    #     rental.status = "CLOSED"
    #     rental.save(update_fields=["returned_at", "status"])

    #     book = rental.book

    #     # 예약만료일 부여
    #     target = Reservation.objects.active().filter(book=book).order_by("reservation_date").first()
    #     if target:
    #         target.due_date = date.today() + timedelta(days=RESERVATION_DAYS)
    #         target.save(update_fields=["due_date"])
    #         # 남은 예약이 있으면
    #         if book.status != "예약중":
    #             book.status = "예약중"
    #             book.save(update_fields=["status"])
    #     else:
    #         # 더 이상 예약이 없으면
    #         if book.status != "대출가능":
    #             book.status = "대출가능"
    #             book.save(update_fields=["status"])