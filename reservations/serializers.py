# reservations/serializers.py
from django.conf import settings
from rest_framework import serializers
from django.utils import timezone
from .models import Reservation

# 설정값 없으면 기본 3권
RES_LIMIT = getattr(settings, 'RESERVATION_LIMIT_PER_USER', 3)

class ReservationSerializer(serializers.ModelSerializer):
    # 요청한 사용자로 자동 세팅
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Reservation
        # 필요 컬럼만 명시 (명시가 관리에 안전). __all__ 써도 되지만 아래 read_only와 충돌 없게만.
        fields = ('id', 'user', 'book', 'status', 'created_at', 'due_date', 'canceled_at')
        # 클라이언트가 바꾸면 안 되는 값들 잠금
        read_only_fields = ('id', 'status', 'created_at', 'canceled_at')
        # 만약 due_date도 서버에서만 정하고 싶으면 위 튜플에 'due_date'도 추가

    def validate(self, attrs):
        """
        - 대출중 도서만 예약 허용
        - 활성 + 미만료 중복 예약 방지
        """
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else attrs.get('user')
        book = attrs.get('book') or getattr(self.instance, 'book', None)

        # 생성/수정 공통 방어
        if not user or not book:
            return attrs

        # ✅ 대출중 도서만 예약 허용
        if getattr(book, 'book_status', None) != '대출중':
            raise serializers.ValidationError('대출중인 도서만 예약할 수 있습니다.')

        # ✅ 중복 예약 방지 (ACTIVE & not expired)
        dup_qs = Reservation.objects.active().not_expired().filter(user=user, book=book)
        if self.instance:
            dup_qs = dup_qs.exclude(pk=self.instance.pk)
        if dup_qs.exists():
            raise serializers.ValidationError('이미 해당 도서를 유효하게 예약 중입니다.')
        
        # ✅ (신규 생성 시) 사용자별 유효 예약 권수 제한
        if not self.instance:
            active_cnt = Reservation.objects.active().not_expired().for_user(user).count()
            if active_cnt >= RES_LIMIT:
                raise serializers.ValidationError(
                    {'non_field_errors': [f'예약은 동시에 최대 {RES_LIMIT}권까지 가능합니다. (현재 {active_cnt}권 보유)']}
                )

        return attrs
    

        today = timezone.localdate()

        qs = Reservation.objects.filter(
            user=user,
            book=book,
            reservation_due_date__gte=today,  # 아직 만료되지 않은 예약 = 유효 예약
        )

        # 자기 자신 업데이트일 땐 제외
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["이미 해당 도서를 예약 중입니다. (만료 전 중복 예약 불가)"]}
            )

        return attrs




