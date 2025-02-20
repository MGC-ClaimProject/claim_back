import logging

import requests
from common.exceptions import UnauthorizedException
from common.logging_config import logger
from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from members.models import Member
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from users.models import User
from users.serializers.oauth_serializers import (KakaoAuthCodeSerializer,
                                                 SocialLoginSerializer)

logger = logging.getLogger("custom_api_logger")


@extend_schema(tags=["Oauth"])
class KakaoLoginCallbackView(APIView):
    """✅ 카카오 로그인 콜백 API"""

    permission_classes = [AllowAny]
    serializer_class = KakaoAuthCodeSerializer

    def get(self, request, *args, **kwargs):
        """✅ 카카오 로그인 후 프론트엔드로 리다이렉트"""
        code = request.GET.get("code")
        frontend_url = f"{settings.FRONTEND_CALLBACK_URL}{code}"
        return redirect(frontend_url)

    def post(self, request, *args, **kwargs):
        """✅ 프론트에서 받은 인가 코드로 카카오에 액세스 토큰 요청"""
        serializer = KakaoAuthCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_data = serializer.save()

        # ✅ 유저가 새로 생성된 경우 201 코드 반환
        user_created = auth_data["user_created"]
        user_id = auth_data["user"]["id"]
        status_code = status.HTTP_201_CREATED if user_created else status.HTTP_200_OK
        user_info = Member.objects.filter(user_id=user_id).first()

        # ✅ 응답 객체 생성
        response = Response(
            {
                "access_token": auth_data["access_token"],
                "user": {
                    "id": auth_data["user"]["id"],  # 기존 user 정보
                    "user_name": user_info.name,  # 추가된 member 정보
                    "member_id": user_info.id,
                },
            },
            status=status_code,
        )

        # ✅ 리프레시 토큰을 HttpOnly 쿠키로 설정
        response.set_cookie(
            key="refresh_token",
            value=auth_data["refresh_token"],
            httponly=False,
            secure=False,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,  # ✅ 7일
        )

        return response


@extend_schema(tags=["Oauth"])
class RefreshAccessTokenAPIView(APIView):
    """리프레시 토큰을 이용한 Access Token 갱신 API View"""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            raise UnauthorizedException(
                "리프레시 토큰이 누락되었습니다.", code="MISSING_REFRESH_TOKEN"
            )

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh.get("user_id")
            user = User.objects.get(id=user_id)

            new_access_token = str(refresh.access_token)

            response_data = {
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": refresh.access_token.payload["exp"],
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except (User.DoesNotExist, TokenError):
            logger.error("리프레시 토큰이 유효하지 않음.")
            raise UnauthorizedException(
                "유효하지 않은 리프레시 토큰입니다.", code="INVALID_REFRESH_TOKEN"
            )


class LogoutView(APIView):
    """사용자 로그아웃 처리 View"""

    permission_classes = (IsAuthenticated,)
    serializer_class = SocialLoginSerializer

    @extend_schema(
        tags=["Oauth"],
        summary="사용자 로그아웃",
        responses={200: {"type": "object", "description": "로그아웃 성공"}},
    )
    def post(self, request, *args, **kwargs):
        access_token = request.headers.get("Authorization")
        if not access_token:
            raise UnauthorizedException(
                "액세스 토큰이 누락되었습니다.", code="MISSING_ACCESS_TOKEN"
            )

        # ✅ 액세스 토큰에서 사용자 ID 추출
        try:
            access_token = access_token.split(" ")[
                1
            ]  # "Bearer <token>"에서 토큰 부분만 추출
            decoded_access_token = AccessToken(access_token)
            user_id = decoded_access_token["user_id"]
        except Exception as e:
            logger.error(f"액세스 토큰 해독 실패: {e}")
            raise UnauthorizedException(
                "유효하지 않은 액세스 토큰입니다.", code="INVALID_ACCESS_TOKEN"
            )

        # ✅ 사용자와 연결된 리프레시 토큰 찾기
        from django.utils.timezone import now

        outstanding_tokens = OutstandingToken.objects.filter(
            user_id=user_id, expires_at__gt=now()
        )

        if outstanding_tokens.exists():
            try:
                for token in outstanding_tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
                    token.delete()  # ✅ DB에서 삭제
            except Exception as e:
                logger.error(f"리프레시 토큰 블랙리스트 처리 중 오류 발생: {e}")
                raise UnauthorizedException(
                    "리프레시 토큰 블랙리스트 처리 중 오류가 발생했습니다.",
                    code="TOKEN_BLACKLIST_ERROR",
                )

        # ✅ 프론트 쿠키에서도 리프레시 토큰 삭제
        response = Response(
            {"detail": "로그아웃에 성공했습니다."}, status=status.HTTP_200_OK
        )
        response.delete_cookie("refresh_token", path="/", domain=settings.SESSION_COOKIE_DOMAIN)
        return response
