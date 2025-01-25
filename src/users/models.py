from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, **kwargs):
        # 이메일이 없는 경우 예외 발생
        if not email:
            raise ValueError("Users must have an email address")

        # 계정을 기본으로 비활성화 상태로 설정
        kwargs.setdefault("is_active", False)
        # 계정의 광고 동의를 기본적으로 비활성화 상태로 설정
        kwargs.setdefault("is_ad_agreed", False)

        # User 모델의 인스턴스를 생성
        user = self.model(
            email=self.normalize_email(email),
            **kwargs,
        )
        # 비밀번호 설정
        password = kwargs.pop("password", "pw123")
        if not password:
            raise ValueError("Users must have a password")
        user.set_password(password)

        # 데이터베이스에 사용자 저장
        user.save(using=self._db)
        return user

    def create_superuser(self, email, **kwargs):
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        # 필수 필드 체크
        if kwargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            **kwargs,
        )


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=100, unique=True)
    social_kakao_id = models.CharField(max_length=100, null=True, blank=True)
    is_ad_agreed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # 관리자 여부
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자들"

    def __str__(self):
        return self.email
