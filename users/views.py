from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserSignupSerializer, UserUpdateSerializer
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth import get_user_model
from .serializers import FindUsernameSerializer

# Create your views here.
User = get_user_model()

# 회원가입
class SignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "회원가입이 완료되었습니다."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 회원정보
class MypageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "user_type": user.user_type,
            "name": user.name,
            "phone" : user.phone
        })
    
    def put(self, request):
        serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=False)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "회원정보가 수정되었습니다.",
                "data": {
                    "username": user.username,
                    "user_type": user.user_type,
                    "name": user.name,
                    "phone": user.phone
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 아이디 찾기
class FindUsernameView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "find_username"

    def post(self, request):
        ser = FindUsernameSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        name = ser.validated_data["name"]
        phone_digits = getattr(ser, "_normalized_phone", None)
        hyphen = f"{phone_digits[:3]}-{phone_digits[3:7]}-{phone_digits[7:]}"
        qs = User.objects.filter(name__iexact=name, phone__in=[phone_digits, hyphen])
        # qs = User.objects.filter(name=name, phone=phone_digits)

        if not qs.exists():
            return Response({"message": "일치하는 회원 정보를 찾을 수 없습니다."},
                            status=status.HTTP_404_NOT_FOUND)

        username = list(dict.fromkeys(qs.values_list("username", flat=True)))

        return Response({
            "message": "아이디 찾기 결과입니다.",
            "username": username
        }, status=status.HTTP_200_OK)