from datetime import datetime, timezone

from common.exceptions import BadRequestException
from common.logging_config import logger
from rest_framework import serializers
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User


class AccessTokenSerializer(serializers.Serializer):
    """
    Access Token 생성 Serializer.
    """

    def create_access_token(self, user):
        """
        새로운 Access Token을 생성.
        """
        if not user:
            raise BadRequestException(
                "유효하지 않은 사용자입니다.", code="INVALID_USER"
            )

        # 새 Access Token 생성
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)


class RefreshTokenSerializer(serializers.Serializer):
    """
    리프레시 토큰 직렬화기
    - 리프레시 토큰의 유효성을 검증하고 새로운 토큰을 발급.
    """

    refresh_token = serializers.CharField(
        max_length=512, write_only=True, help_text="발급된 리프레시 토큰"
    )

    def validate_refresh_token(self, value):
        """
        리프레시 토큰 유효성 검증
        """
        if not value:
            raise BadRequestException(
                "리프레시 토큰이 필요합니다.", code="MISSING_REFRESH_TOKEN"
            )

        if len(value) > 512:
            raise BadRequestException(
                "리프레시 토큰의 길이가 너무 깁니다.", code="REFRESH_TOKEN_TOO_LONG"
            )

        try:
            token = RefreshToken(value)
        except Exception as e:
            raise BadRequestException(
                "유효하지 않은 리프레시 토큰입니다.", code="INVALID_REFRESH_TOKEN"
            ) from e

        exp_timestamp = token["exp"]
        current_time = datetime.now(tz=timezone.utc).timestamp()
        if current_time >= exp_timestamp:
            raise BadRequestException(
                "리프레시 토큰이 만료되었습니다.", code="REFRESH_TOKEN_EXPIRED"
            )

        return value

    def create_refresh_token(self, user):
        """
        기존 리프레시 토큰을 제거하고 새로운 리프레시 토큰 생성.
        """
        self._blacklist_existing_refresh_tokens(user)
        refresh = RefreshToken.for_user(user)
        return str(refresh)

    def _blacklist_existing_refresh_tokens(self, user):
        """
        사용자의 기존 리프레시 토큰을 블랙리스트에 추가.
        """
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        for token in outstanding_tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception as e:
                logger.error(f"리프레시 토큰 블랙리스트 처리 중 오류 발생: {str(e)}")
        outstanding_tokens.delete()


class SocialLoginSerializer(serializers.Serializer):
    """소셜 로그인 공통 시리얼라이저"""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not value:
            raise BadRequestException(
                "사용자 이메일이 제공되지 않았습니다.", code="missing_email"
            )
        return value

    def save(self, **kwargs):
        """
        사용자 생성 또는 업데이트
        - 이메일을 기준으로 사용자 정보를 저장하거나 기존 사용자 업데이트.
        """
        validated_data = {**self.validated_data, **kwargs}
        email = validated_data["email"]

        # 이메일을 기준으로 사용자 검색
        user, created = User.objects.get_or_create(email=email)

        # ✅ 로그인 성공 시 `is_active = True`로 설정
        if not user.is_active:
            user.is_active = True
            user.save()

        # 기존 리프레시 토큰 블랙리스트 처리
        self._blacklist_existing_refresh_tokens(user)

        return user

    def _blacklist_existing_refresh_tokens(self, user):
        """
        유저의 기존 리프레시 토큰을 블랙리스트 처리.
        """
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        for token in outstanding_tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception as e:
                logger.error(f"토큰 블랙리스트 처리 중 오류 발생: {str(e)}")
        outstanding_tokens.delete()
