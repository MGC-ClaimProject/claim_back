from datetime import datetime, timezone

import requests
from common.exceptions import BadRequestException
from common.logging_config import logger
from django.conf import settings
from members.models import Member
from rest_framework import serializers
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from users.serializers.user_serializers import UserSerializer


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
        """✅ 카카오 인가 코드 유효성 검증"""
        if not value:
            raise BadRequestException("인가 코드가 없습니다.", code="MISSING_AUTH_CODE")
        return value

    def exchange_code_for_access_token(self, code):
        """✅ 카카오 인가 코드를 사용하여 액세스 토큰 요청"""
        token_url = settings.KAKAO_TOKEN_URL
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
            raise BadRequestException(
                "카카오 액세스 토큰 요청 실패", code="KAKAO_TOKEN_ERROR"
            )

        return data["access_token"]

    def get_kakao_user_info(self, access_token):
        """✅ 카카오 API에서 사용자 정보 가져오기"""
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.get(user_info_url, headers=headers)
        user_data = response.json()

        kakao_id = user_data.get("id")
        email = user_data.get("kakao_account", {}).get("email", None)
        name = user_data.get("kakao_account", {}).get("name", None)
        phone = (
            user_data.get("kakao_account", {})
            .get("phone_number", "")
            .replace("+82 ", "0")
        )  # 한국 번호 변환
        gender = user_data.get("kakao_account", {}).get("gender", None)  # male, female
        birth = user_data.get("kakao_account", {}).get("birthday", None)  # MMDD 형태

        # ✅ 성별 변환 (카카오: male/female → 시스템: Male/Female)
        gender_mapping = {"male": "Male", "female": "Female"}
        gender = gender_mapping.get(gender, "Other")

        # ✅ 생년월일 변환 (YYYY-MM-DD 형식)
        birth_year = user_data.get("kakao_account", {}).get("birthyear", None)
        if birth_year and birth:
            birth = f"{birth_year}-{birth[:2]}-{birth[2:]}"  # "YYYY-MM-DD" 형식
        else:
            birth = datetime.today().strftime("%Y-%m-%d")  # ✅ 오늘 날짜 사용

        if not kakao_id or not email:
            raise BadRequestException(
                "카카오 사용자 정보를 가져올 수 없습니다.", code="KAKAO_USER_INFO_ERROR"
            )

        return {
            "kakao_id": kakao_id,
            "email": email,
            "name": name,
            "phone": phone,
            "gender": gender,
            "birth": birth,
        }

    def get_or_create_user(self, email):
        """✅ 기존 유저 확인 및 생성"""
        user, created = User.objects.get_or_create(
            email=email, defaults={"is_active": True}
        )
        return user, created

    def create_member(self, user, kakao_data):
        # `user` 값으로 기존 Member 객체 조회
        member = Member.objects.filter(user=user).first()

        # 존재하지 않는 경우 새로 생성
        if not member:
            member = Member.objects.create(
                user=user,
                name=kakao_data.get("name", ""),
                phone=kakao_data.get("phone", ""),
                birth=kakao_data.get("birth", ""),
                gender=kakao_data.get("gender", "unknown"),
                relation="Self",
            )

        return member

    def create_tokens(self, user):
        """✅ JWT 토큰 발급"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }

    def save(self, **kwargs):
        """✅ 카카오 로그인 전체 프로세스 수행"""
        code = self.validated_data["code"]

        # 1️⃣ 액세스 토큰 발급
        access_token = self.exchange_code_for_access_token(code)

        # 2️⃣ 사용자 정보 가져오기
        kakao_data = self.get_kakao_user_info(access_token)

        # 3️⃣ 기존 사용자 조회 및 생성
        user, user_created = self.get_or_create_user(kakao_data["email"])

        # 4️⃣ Member 생성 또는 업데이트
        member = self.create_member(user, kakao_data)

        # 5️⃣ JWT 토큰 발급
        tokens = self.create_tokens(user)

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": UserSerializer(user).data,
            "member": {
                "id": member.id,
                "name": member.name,
                "phone": member.phone,
                "birth": member.birth,
                "gender": member.gender,
                "relation": member.relation,
            },
            "user_created": user_created,  # ✅ 유저 생성 여부 추가
        }
