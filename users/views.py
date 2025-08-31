from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSignupSerializer, UserUpdateSerializer

# Create your views here.
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