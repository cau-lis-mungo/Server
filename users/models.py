from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# Create your models here.
# 사용자 상태
class UserStatus(models.Model):
    rental_total = models.IntegerField(null=True, blank=True)
    reservation_total = models.IntegerField(null=True, blank=True)
    over_due_total = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Status {self.pk} (대출: {self.rental_total}, 예약: {self.reservation_total}, 연체: {self.over_due_total})"

# 커스텀 사용자 매니저
class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username must be provided")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

# 사용자
class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('재학생', '재학생'),
        ('재적생', '재적생'),
        ('타과생', '타과생'),
    ]

    username = models.CharField(max_length=20, unique=True)  # 아이디
    name = models.CharField(max_length=20) # 이름
    phone = models.CharField(max_length=20) # 전화번호
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES) # 회원 구분
    status = models.ForeignKey(UserStatus, on_delete=models.SET_NULL, null=True, blank=False) # 상태

    # Django 권한 시스템용 필드
    is_active = models.BooleanField(default=True) # 활성화 여부
    is_staff = models.BooleanField(default=False) # 관리자 여부

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'user_type']

    def __str__(self):
        return self.username