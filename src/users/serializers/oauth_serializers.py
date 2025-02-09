from datetime import datetime, timezone

from common.exceptions import BadRequestException
from common.logging_config import logger
from rest_framework import serializers
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User


import requests
from django.conf import settings
from users.serializers.user_serializers import UserSerializer



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




class KakaoAuthCodeSerializer(serializers.Serializer):
    """✅ 카카오 로그인 인가 코드 요청을 처리하는 Serializer"""

    code = serializers.CharField(required=True, help_text="카카오 인가 코드")

    def validate_code(self, value):
        """
        ✅ 카카오 인가 코드 유효성 검증
        """
        if not value:
            raise BadRequestException("인가 코드가 없습니다.", code="MISSING_AUTH_CODE")
        return value

    def exchange_code_for_access_token(self, code):
        """
        ✅ 카카오 인가 코드를 사용하여 액세스 토큰 요청
        """
        token_url = "https://kauth.kakao.com/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_CALLBACK_URL,
            "code": code,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(token_url, data=payload, headers=headers)
        data = response.json()

        if "access_token" not in data:
            raise BadRequestException("카카오 액세스 토큰 요청 실패", code="KAKAO_TOKEN_ERROR")

        return data["access_token"]

    def get_kakao_user_info(self, access_token):
        """
        ✅ 카카오 API에서 사용자 정보 가져오기
        """
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(user_info_url, headers=headers)
        user_data = response.json()

        kakao_id = user_data.get("id")
        email = user_data.get("kakao_account", {}).get("email", None)

        if not kakao_id:
            raise BadRequestException("카카오 사용자 정보를 가져올 수 없습니다.", code="KAKAO_USER_INFO_ERROR")

        return kakao_id, email

    def get_or_create_user(self, kakao_id, email):
        """
        ✅ 기존 유저 확인 및 생성
        """
        # ✅ 1. social_kakao_id가 있는 유저 확인
        user = User.objects.filter(social_kakao_id=kakao_id).first()
        if user:
            return user  # ✅ 기존 계정 사용

        # ✅ 2. 기존 이메일이 있는 유저 확인 후 social_kakao_id 업데이트
        user = User.objects.filter(email=email).first()
        if user:
            user.social_kakao_id = kakao_id
            user.save()
            return user

        # ✅ 3. 새로운 유저 생성
        user = User.objects.create(
            email=email,
            social_kakao_id=kakao_id,
            is_active=True  # 기본 활성화
        )
        return user

    def create_tokens(self, user):
        """
        ✅ JWT 토큰 발급
        """
        refresh = RefreshToken.for_user(user)
        return {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }

    def save(self, **kwargs):
        """
        ✅ 카카오 로그인 전체 프로세스 수행
        """
        code = self.validated_data["code"]

        # 1️⃣ 액세스 토큰 발급
        access_token = self.exchange_code_for_access_token(code)

        # 2️⃣ 사용자 정보 가져오기
        kakao_id, email = self.get_kakao_user_info(access_token)

        # 3️⃣ 기존 사용자 조회 및 생성
        user = self.get_or_create_user(kakao_id, email)

        # 4️⃣ JWT 토큰 발급
        tokens = self.create_tokens(user)

        from users.serializers.user_serializers import UserSerializer
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": UserSerializer(user).data,
        }