from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Reservation
from .serializers import ReservationCreateSerializer, ReservationSerializer

# 예약 접근 권한
class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user_id == request.user.id

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related("book", "user")
    
    def get_permissions(self):
        base = [permissions.IsAuthenticated()]
        if self.action in ["retrieve", "destroy", "cancel"]:
            base.append(IsAdminOrOwner())
        return base

    # 생성
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        read_serializer = ReservationSerializer(instance, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    # 예약 조회
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff and self.request.query_params.get("all") == "true":
            return qs
        return qs.filter(user=self.request.user)
    
    # 예약 생성
    def get_serializer_class(self):
        if self.action == "create":
            return ReservationCreateSerializer
        return ReservationSerializer
    
    # 예약 취소
    def perform_destroy(self, instance):
        instance.cancel()

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        self.check_object_permissions(request, reservation)
        reservation.cancel()
        return Response({"message": "예약이 취소되었습니다."}, status=status.HTTP_200_OK)