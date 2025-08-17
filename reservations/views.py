# reservations/views.py (발췌)
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Reservation
from .serializers import ReservationSerializer

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = Reservation.objects.for_user(self.request.user)
        # 게으른 만료 처리
        qs.filter(status='ACTIVE', due_date__lt=timezone.now()).update(status='EXPIRED')

        # 선택 필터
        status_param = self.request.query_params.get('status')
        if status_param in ('ACTIVE', 'CANCELED', 'EXPIRED'):
            qs = qs.filter(status=status_param)
        if self.request.query_params.get('active_only') in ('1', 'true', 'True'):
            qs = qs.filter(status='ACTIVE', due_date__gte=timezone.now())
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.refresh_and_mark_expired(save=True)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        권장 정책: 멱등 응답
        - ACTIVE면 취소 수행 → 200
        - 이미 CANCELED/EXPIRED여도 → 200 (상태만 알려줌)
        """
        reservation = self.get_object()           # IsOwner로 본인 것만
        reservation.refresh_and_mark_expired(save=True)  # 최신 만료 반영

        changed = reservation.cancel()            # bool 반환(권장 모델 구현)
        if changed:
            return Response(
                {
                    'detail': '예약을 취소했습니다.',
                    'status': reservation.status,
                    'canceled_at': reservation.canceled_at
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'detail': '이미 취소되었거나 만료된 예약입니다.',
                    'status': reservation.status
                },
                status=status.HTTP_200_OK
            )




