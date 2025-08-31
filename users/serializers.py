from rest_framework import serializers
from .models import User
import re
from django.contrib.auth import get_user_model

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
            raise serializers.ValidationError({"message": "이미 존재하는 아이디입니다."})
        return value
    
    def validate_phone(self, value):
        digits = re.sub(r'[^0-9]', '', value)
        if not (len(digits) == 11 and digits.startswith('010')):
            raise serializers.ValidationError({"message": "전화번호 형식이 올바르지 않습니다. 예) 010-1234-5678"})
        return digits #value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

# 회원정보 수정
class UserUpdateSerializer(serializers.ModelSerializer):
    # username은 수정 불가
    username = serializers.ReadOnlyField()

    name = serializers.CharField(
        required=True,
        error_messages={"required": "이름을 입력해주세요."}
    )
    phone = serializers.CharField(
        required=True,
        error_messages={"required": "전화번호를 입력해주세요."}
    )
    user_type = serializers.ChoiceField(
        required=True,
        choices=User.USER_TYPE_CHOICES,
        error_messages={"required": "회원 구분을 선택해주세요."}
    )

    # 비밀번호 변경
    current_password = serializers.CharField(
        write_only=True, required=False, style={'input_type': 'password'}
    )
    password = serializers.CharField(
        write_only=True, required=False, min_length=8, style={'input_type': 'password'},
        # error_messages={"message": "비밀번호는 최소 8자 이상이어야 합니다."}
        error_messages={
            "min_length": "비밀번호는 최소 8자 이상이어야 합니다.",
            "required": "비밀번호를 입력해주세요."}
    )

    class Meta:
        model = User
        fields = (
            'username',
            'name', 'phone', 'user_type',
            'current_password', 'password',
        )

    def validate(self, attrs):
        if 'username' in self.initial_data:
            raise serializers.ValidationError({"message": "아이디는 수정할 수 없습니다."})

        # 비밀번호 변경 시 현재 비밀번호 확인
        new_pw = attrs.get('password')
        if new_pw is not None:
            curr = attrs.get('current_password')
            if not curr:
                raise serializers.ValidationError({"message": "현재 비밀번호를 입력해주세요."})
            if not self.instance.check_password(curr):
                raise serializers.ValidationError({"message": "현재 비밀번호가 올바르지 않습니다."})
        return attrs

    def validate_phone(self, value):
        if value:
            digits = re.sub(r'[^0-9]', '', value)
            if not (len(digits) == 11 and digits.startswith('010')):
                raise serializers.ValidationError({"message": "전화번호 형식이 올바르지 않습니다. 예) 010-1234-5678"})
        return digits #value

    def update(self, instance, validated_data):
        new_pw = validated_data.pop('password', None)
        validated_data.pop('current_password', None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        if new_pw:
            instance.set_password(new_pw)

        instance.save()
        return instance