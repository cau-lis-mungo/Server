from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSignupSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from common.swagger import ok_response, ErrorSchema, AUTH_HEADER

# Create your views here.
# 회원가입
class SignupView(APIView):
    @swagger_auto_schema(
        operation_summary="회원가입",
        request_body=UserSignupSerializer,
        responses={
            201: ok_response("회원가입 성공", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={"message": openapi.Schema(type=openapi.TYPE_STRING)}
            )),
            400: ErrorSchema
        },
        tags=["Auth"]
    )
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "회원가입이 완료되었습니다."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 회원정보
class MypageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="내 정보 조회",
        manual_parameters=[AUTH_HEADER],
        responses={
            200: ok_response("내 정보", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                    "user_type": openapi.Schema(type=openapi.TYPE_STRING),
                    "name": openapi.Schema(type=openapi.TYPE_STRING),
                    "phone": openapi.Schema(type=openapi.TYPE_STRING),
                }
            )),
            401: ErrorSchema
        },
        tags=["Auth"]
    )
    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "user_type": user.user_type,
            "name": user.name,
            "phone" : user.phone
        })