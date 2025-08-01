from rest_framework import serializers
from .models import User

class UserSignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[],  # 기본 UniqueValidator 제거
        error_messages={"required": "아이디를 입력해주세요."}
    )
    password = serializers.CharField(
        write_only=True, # 응답에 비밀번호가 반환되지 않도록
        min_length=8,
        style={'input_type': 'password'},
        error_messages={
            "required": "비밀번호를 입력해주세요.",
            "min_length": "비밀번호는 최소 8자 이상이어야 합니다."
        }
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'name', 'phone', 'user_type')
        extra_kwargs = {
            # 'username': {
            #     'error_messages': {
            #         'required': "아이디를 입력해주세요."
            #     }
            # },
            'name': {'error_messages': {'required': "이름을 입력해주세요."}},
            'phone': {'error_messages': {'required': "전화번호를 입력해주세요."}},
            'user_type': {'error_messages': {'required': "회원 구분을 선택해주세요."}},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 존재하는 아이디입니다.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user
